from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import database  # database.py
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
SECRET_KEY = "your_secret_key"  # 请替换为安全的密钥

# ————————————————————

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
# flask 全局参数, 用来保存上传的文件的位置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---- 测试接口 ----
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")


# ---- 登录接口（查数据库 user_info）----
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if role not in ["staff", "admin"]:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    user = database.get_user(username)
    if user and user["password"] == password:
        # 注意：user_info 表应有 role 字段！否则可用 identity/is_admin 判断
        db_role = "admin" if user.get("is_admin") == 1 else "staff"
        if db_role != role:
            return jsonify({"success": False, "message": "Invalid role"}), 400
        user_obj = {
            "id": user["user_id"],
            "username": user["user_id"],
            "role": db_role,
            "subrole": user.get("role")
        }
        payload = {
            **user_obj,
            # "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # 可选
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({
            "success": True,
            "token": token,
            "user": user_obj
        })
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401
    
@app.route('/api/start_session', methods=['POST'])
def api_start_session():
    data = request.json
    user_id = data['user_id']
    title = data.get('title', 'Untitled Session')
    session_id, error = database.start_session_db(user_id, title)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"session_id": session_id})

@app.route('/api/add_message', methods=['POST'])
def api_add_message():
    data = request.json
    ok, error = database.add_message_db(data['session_id'], data['role'], data['content'])
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Message added successfully"})

@app.route('/api/get_messages/<session_id>', methods=['GET'])
def api_get_messages(session_id):
    messages, error = database.get_messages_db(session_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(messages)


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

# ---- 获取用户个人资料接口 ----
@app.route('/api/profile', methods=['GET'])
def get_profile():
    # 1. 从请求头中获取 Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Authorization header is missing or invalid"}), 401

    # 2. 提取并解码 JWT token
    token = auth_header.split(" ")[1]
    try:
        # 使用在文件顶部定义的 SECRET_KEY 解码
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # 从 token 的载荷中获取 user_id（在登录时我们存的是'id'）
        user_id = payload.get('id')
        if not user_id:
            raise jwt.InvalidTokenError("Token payload is missing user ID")

    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Invalid token"}), 401

    # 3. 使用 user_id 从数据库中查询用户信息
    user_data = database.get_user(user_id)
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404

    # 4. 整理并返回个人资料信息（不包含密码等敏感信息）
    profile_info = {
        "userId": user_data.get("user_id"),
        "firstName": user_data.get("first_name"),
        "lastName": user_data.get("last_name"),
        "email": user_data.get("email"),
        "phone": user_data.get("phone"),
        "department": user_data.get("department"),
        "role": user_data.get("role")  # 这是详细的角色，如 'PhD Student', 'Tutor'
    }

    return jsonify({"success": True, "profile": profile_info})

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
    session_id = data.get('session_id', None)     # 需要前端传递
    user_id = data.get('user_id', None) # <<<<<<<<<<<<<<<< 获取 user_id
    user_role = data.get('role', 'user')

    if not question:
        return jsonify({"error": "question 不能为空"}), 400
    
    if not all([question, session_id, user_id]):
        return jsonify({"error": "question, session_id, and user_id are required"}), 400

    # 在写入消息前，检查并创建会话历史
    ok, err = database.check_or_create_session(session_id, user_id, title=f"Chat on {datetime.now().strftime('%Y-%m-%d')}")
    if not ok:
        return jsonify({"error": f"Failed to ensure session exists: {err}"}), 500

    # 1. 写入用户提问到数据库
    _, user_err = database.add_message_db(session_id, user_role, question)

    # 2. 生成AI回复（你的原有payload代码）
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

    # 3. 写入AI回复到数据库
    _, ai_err = database.add_message_db(session_id, "ai", answer)
    
    return jsonify({"answer": answer})

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
