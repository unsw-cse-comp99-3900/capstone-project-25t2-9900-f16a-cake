from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from search import extract_keywords, multi_hot_encode, calculate_similarity, DATABASE
import requests
# v 生成 token 的库 v
import jwt
import datetime
# ^ 生成 token 的库 ^

# —————————rag———————————
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)
# ———— AI 聊天配置区域 ————
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/QwQ-32B"
API_KEY = "sk-xlrowobsoqpeykasamsgwlbjiilruinjklvbryuvbiukhekt"

# 生成 token 的密钥
SECRET_KEY = "hdingo_secret_key"  

# ————————————————————

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
# flask 全局参数, 用来保存上传的文件的位置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---- 测试接口 ----
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")


# ---- 假用户数据 ----
fake_users = [
    {
        "id": 1,
        "username": "phd1",
        "password": "pass123",
        "email": "staff1@example.com",
        "role": "staff",
        "subrole": "phd", 
        "firstName": "Jiaxin", 
        "lastName": "Weng", 
        "phone": "0413962xxx", 
        "department": "CSE"
    },
    {
        "id": 2, 
        "username": "tutor1", 
        "password": "pass123", 
        "email": "staff2@example.com", 
        "role": "staff", 
        "subrole": "tutor", 
        "firstName": "Vincent", 
        "lastName": "Nono", 
        "phone": "0413123xxx", 
        "department": "CSE"
    },
    {   
        "id": 3, 
        "username": "lecturer1", 
        "password": "pass123", 
        "email": "staff3@example.com", 
        "role": "staff", 
        "subrole": "lecturer", 
        "firstName": "Alice", 
        "lastName": "Smith", 
        "phone": "0413999xxx", 
        "department": "CSE"
    },
    {
        "id": 4,
        "username": "admin1", 
        "password": "adminpass", 
        "email": "admin1@example.com", 
        "role": "admin", 
        "subrole": None, 
        "firstName": "Admin", 
        "lastName": "User", 
        "phone": "0413888xxx", 
        "department": "CSE"
    },
    # 可以继续添加更多账号
]


# ---- 登录接口, 现在使用 JWT 登录, 用于后期鉴权 ----
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username") # 前端给的 username
    password = data.get("password") # 前端给的 password
    role = data.get("role") # 前端想要以 staff 或 admin 登录

    # 检查 role 是否为 staff 或 admin，否则返回 400
    if role not in ["staff", "admin"]:
        return jsonify({"success": False, "message": "Invalid role"}), 400
    
    # 模拟查找用户，如果用户存在且密码正确，则返回成功
    user = next((u for u in fake_users if u["username"] == username), None)
    if user and user["password"] == password:
        if (role == "staff" and user["role"] == "staff") or (role == "admin" and user["role"] == "admin"):
            user_obj = {
                "id": user["id"],  # 修正：用当前用户的 id
                "username": user["username"],
                "role": user["role"],
                "subrole": user["subrole"]
            }
            payload = {
                "id": user_obj["id"],
                "username": user_obj["username"],
                "role": user_obj["role"],
                "subrole": user_obj["subrole"],
                # 暂时不设置过期时间, 后期需要再设置
                # "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify({
                "success": True,
                "token": token,
                "user": user_obj
            })
        else:
            return jsonify({"success": False, "message": "Invalid role"}), 400
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401


# ---- SSO登录模拟 ----
@app.route('/api/sso-login', methods=['GET'])
def sso_login():
    # 实际项目会重定向到UNSW SSO登录页，这里仅做演示，直接"登录成功"
    # 可以考虑带一个 ?next= 参数指明回跳页面
    return jsonify({"success": True, "role": "staff", "message": "SSO Login success!"})


# ---- search接口 ----
@app.route('/api/search', methods=['POST'])
def search_api():
    data = request.get_json()
    query = data.get("query", "").strip()

    # 关键词提取和多热编码
    extracted = extract_keywords(query)
    query_encoded = multi_hot_encode(extracted)

    # 遍历所有条目，计算分数
    results = []
    for item in DATABASE:
        score = calculate_similarity(query_encoded, item["keywords_encoded"], query, item["title"])
        results.append({
            "title": item["title"],
            "pdf_path": item.get("pdf_path", ""),
            "score": score,
            "year": item.get("year", "")
        })

    # 按分数排序，只返回相关度>0的前5个
    filtered = sorted([r for r in results if r["score"] >= 0], key=lambda x: x["score"], reverse=True)[:5]

    return jsonify({"results": filtered})


# ---- 首页（仅演示跳转用）----
@app.route('/')
def home():
    return 'Welcome to the demo backend!'

def rag_search(question):
    # 1. 加载模型
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 2. 加载 Faiss 索引
    index = faiss.read_index("rag/zid_faq.index")

    # 3. 加载 ID 映射
    with open("rag/zid_faq_ids.pkl", "rb") as f:
        ids = pickle.load(f)

    import json

    with open("rag/zid_faq_docs.json", "r", encoding="utf-8") as f:
        docs = json.load(f)

    def retrieve(query, top_k=5, score_threshold=0.8):
        q_emb = model.encode([query])
        D, I = index.search(np.array(q_emb, dtype="float32"), top_k)

        results = []
        for dist, idx in zip(D[0], I[0]):
            score = float(dist)
            if score > score_threshold:
                continue
            doc_id = ids[idx]
            entry = next(d for d in docs if d["id"] == doc_id)
            results.append({
                "score": score,
                "question": entry["question"],
                "answer": entry["answer"]
            })
        return results

    hits = retrieve(question, top_k=10, score_threshold=0.75)
    threshold = 0.8
    filtered = [h for h in hits if h["score"] >= threshold]
    if not filtered:
        result_str = "No results above score 0.8."
    else:
        parts = []
        for i, hit in enumerate(filtered, 1):
            parts.append(
                f"{i}. Question: {hit['question']}\n"
                f"   Answer:   {hit['answer']}"
            )
        # 每条之间用两个换行分隔
        result_str = "\n\n".join(parts)
    return result_str
    
# ---- AI 聊天接口 ----
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "question 不能为空"}), 400
    knowlegde=rag_search(question)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are AI assistance called ‘HDingo's Al chat bot’, an AI designed to "
                                          "help new faculty, staff, and students in the School of Computer Science "
                                          "and Engineering (CSE) complete their onboarding tasks. Your objectives "
                                          "are:1. 快速、准确地回答关于入职流程、政策、资源、系统使用等方面的问题；2. "
                                          "在回答中引用最新且经过审核的文档内容，保证信息一致性与权威性；3. 如果遇到不明确或超出权限的问题，引导用户提交 IT 工单或联系相关部门；4. "
                                          "对话风格：专业、简洁、友好、易理解并且使用英语作为主要用语。你拥有以下能力：- 结合检索到的文档段落进行动态回答（RAG-Sequence / RAG-Token）；- "
                                          "根据用户不同角色（教职工/学生/管理员）提供差异化视图和链接；- 支持文件上传下载、关键词搜索、反馈收集等功能调用。"
                                         },
            {"role": "user", "content": "please answer the question:"+question+"based on the:"+knowlegde}

        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 调用 SiliconFlow API
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    # 提取回答
    answer = result['choices'][0]['message']['content'].strip()
    return jsonify({"answer": answer})

# 获取 staff profile, (现在是模拟数据), 需要后端做鉴权, 从数据库中获取
@app.route('/api/profile', methods=['GET'])
def get_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    user_id = payload.get("id")
    user = next((u for u in fake_users if u.get("id") == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "firstName": user.get("firstName"),
        "lastName": user.get("lastName"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "department": user.get("department"),
        "role": user.get("subrole")
    })

@app.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('pdfs', filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    # 前端没有发文件部分给后端
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    # 后端拿到文件
    file = request.files['file']
    # 前端发过来的文件部分不包含文件
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    # 如果有文件并且是 pdf 文件
    if file and allowed_file(file.filename):
        filename = file.filename
        save_path = os.path.join(str(app.config['UPLOAD_FOLDER']), str(filename))
        file.save(save_path)
        return jsonify({'success': True, 'message': '上传成功', 'filename': filename})
    else:
        return jsonify({'success': False, 'message': '只允许上传 PDF 文件'}), 400

# 获取所有pdf文件
@app.route('/api/admin/getpdfs', methods=['GET'])
def list_pdfs():
    pdf_dir = app.config['UPLOAD_FOLDER']
    pdfs = []
    for fname in os.listdir(pdf_dir):
        if fname.lower().endswith('.pdf'):
            fpath = os.path.join(pdf_dir, fname)
            stat = os.stat(fpath)
            pdfs.append({
                'filename': fname,
                'size': stat.st_size,
                # 文件的上传时间
                'upload_time': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
    return jsonify({'success': True, 'pdfs': pdfs})

# 删除指定pdf文件
@app.route('/api/admin/deletepdf/<filename>', methods=['DELETE'])
def delete_pdf(filename):
    if not filename or not filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400
    pdf_dir = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(pdf_dir, filename)
    if not os.path.isfile(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    try:
        os.remove(file_path)
        return jsonify({'success': True, 'message': 'PDF deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
