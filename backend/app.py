from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from search import extract_keywords, multi_hot_encode, calculate_similarity, DATABASE
import requests
# v 生成 token 的库 v
import jwt
import datetime  # 用于 JWT 过期时间等
# ^ 生成 token 的库 ^

# —————————rag———————————
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import json
from datetime import datetime  # 用于文件时间展示
import time
import random

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
]


# ---- 登录接口 (JWT) ----
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if role not in ["staff", "admin"]:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    user = next((u for u in fake_users if u["username"] == username), None)
    if user and user["password"] == password:
        if (role == "staff" and user["role"] == "staff") or (role == "admin" and user["role"] == "admin"):
            user_obj = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "subrole": user["subrole"]
            }
            payload = {
                "id": user_obj["id"],
                "username": user_obj["username"],
                "role": user_obj["role"],
                "subrole": user_obj["subrole"],
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
    return jsonify({"success": True, "role": "staff", "message": "SSO Login success!"})


# ---- search接口 ----
@app.route('/api/search', methods=['POST'])
def search_api():
    data = request.get_json()
    query = data.get("query", "").strip()

    extracted = extract_keywords(query)
    query_encoded = multi_hot_encode(extracted)

    results = []
    for item in DATABASE:
        score = calculate_similarity(query_encoded, item["keywords_encoded"], query, item["title"])
        results.append({
            "title": item["title"],
            "pdf_path": item.get("pdf_path", ""),
            "score": score,
            "year": item.get("year", "")
        })

    filtered = sorted([r for r in results if r["score"] >= 0], key=lambda x: x["score"], reverse=True)[:5]

    return jsonify({"results": filtered})


# ---- 首页（仅演示跳转用）----
@app.route('/')
def home():
    return 'Welcome to the demo backend!'


# ---------------- RAG -----------------
def rag_search(question):
    # 注意：生产环境最好把以下加载放到全局，只加载一次
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("rag/zid_faq.index")
    with open("rag/zid_faq_ids.pkl", "rb") as f:
        ids = pickle.load(f)
    with open("rag/zid_faq_docs.json", "r", encoding="utf-8") as f:
        docs = json.load(f)

    doc_map = {d["id"]: d for d in docs}

    def retrieve(query, top_k=5, score_threshold=0.8):
        q_emb = model.encode([query])
        D, I = index.search(np.array(q_emb, dtype="float32"), top_k)

        results = []
        for dist, idx in zip(D[0], I[0]):
            score = float(dist)  # 距离越小越相似
            if score > score_threshold:
                continue
            entry = doc_map[ids[idx]]
            src = entry.get("source", {}) or {}
            results.append({
                "score": score,
                "question": entry.get("question", ""),
                "answer": entry.get("answer", ""),
                "title": src.get("title", ""),
                "url": src.get("url", "")
            })
        return results

    hits = retrieve(question, top_k=10, score_threshold=0.75)

    if not hits:
        return "No results above score 0.75.", {}

    parts = []
    ref_dict = {}
    for i, h in enumerate(hits, 1):
        parts.append(
            f"{i}. Question: {h['question']}\n"
            f"   Answer:   {h['answer']}"
        )
        if h["url"]:
            ref_dict[h["title"]] = h["url"]

    knowledge_str = "\n\n".join(parts)
    return knowledge_str, ref_dict


def try_load_json(text: str):
    """优先解析模型输出为 JSON，失败则返回 None 和异常"""
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, e


# ---- AI 聊天接口 ----
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "question 不能为空"}), 400

    knowledge, reference = rag_search(question)

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AI assistance called 'HDingo's Al chat bot', an AI designed to help new faculty, staff, and "
                    "students in the School of Computer Science and Engineering (CSE) complete their onboarding tasks.\n"
                    "Objectives:\n"
                    "1. Answer questions quickly and accurately about onboarding processes, policies, resources, and systems.\n"
                    "2. Cite the newest audited docs for consistency and authority.\n"
                    "3. If unclear/out of scope, guide user to submit an IT ticket or contact dept.\n"
                    "4. Style: professional, concise, friendly, easy to understand, and *in English*.\n\n"
                    "You must return ONLY valid JSON with two keys:\n"
                    "  - \"answer\": string (the final answer)\n"
                    "  - \"reference\": object (mapping title -> url of cited docs)\n"
                    "Do not include code fences. Do not include any additional keys."
                )
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nRelevant knowledge:\n{knowledge}"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
        # 若 API 支持，建议打开：
        # "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    content = result['choices'][0]['message']['content'].strip()

    data_json, err = try_load_json(content)
    if data_json is not None:
        answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if not model_ref:
            model_ref = reference
        return jsonify({"answer": answer, "reference": model_ref})

    # Fallback：模型没按 JSON 格式返回
    return jsonify({"answer": content, "reference": reference})


# 获取 staff profile, (现在是模拟数据), 鉴权已经做了, 后续改成从真实数据库中获取即可
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
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
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


@app.route('/api/aichat/general', methods=['POST'])
def aichat_general():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "question cannot be empty"}), 400
    time.sleep(random.uniform(0.5, 1.5))  # 模拟AI延迟
    return jsonify({"answer": f"This is a mock AI reply: {question}"})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
