from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import database  # database.py
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
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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

# 这个 api 接口可以删除, 前端用不到, 但是 api_add_message 方法需要保留
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

@app.route('/api/get_sessions/<user_id>', methods=['GET'])
def api_get_sessions(user_id):
    sessions, error = database.get_sessions_db(user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(sessions)


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


# ---------------- RAG -----------------
def rag_search(question):
    # 注意：生产环境最好把以下加载放到全局，只加载一次
    index_path = os.path.join(BASE_DIR, "rag", "zid_faq.index")
    # print(f"[DEBUG] Loading FAISS index from: {index_path}")
    index = faiss.read_index(index_path)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    # index = faiss.read_index("rag/zid_faq.index")
    # 加载 ID 列表
    ids_path = os.path.join(BASE_DIR, "rag", "zid_faq_ids.pkl")
    with open(ids_path, "rb") as f:
        ids = pickle.load(f)

    # 加载文档内容
    docs_path = os.path.join(BASE_DIR, "rag", "zid_faq_docs.json")
    with open(docs_path, "r", encoding="utf-8") as f:
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
    session_id = data.get('session_id', None)
    user_id = data.get('user_id', None)
    user_role = data.get('role', 'user')

    if not all([question, session_id, user_id]):
        return jsonify({"error": "question, session_id, and user_id are required"}), 400

    # 在写入消息前，检查并创建会话历史
    ok, err = database.check_or_create_session(session_id, user_id, title=f"Chat on {datetime.now().strftime('%Y-%m-%d')}")
    if not ok:
        return jsonify({"error": f"Failed to ensure session exists: {err}"}), 500

    # 1. 写入用户提问到数据库
    _, user_err = database.add_message_db(session_id, user_role, question)
    if user_err:
        # 即使写入失败，也可以选择继续，但最好记录日志
        print(f"Error writing user message to DB: {user_err}")


    # 2. RAG 检索
    knowledge, reference = rag_search(question)
    
    # 3. 构造并请求 LLM
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
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    # 4. 解析 LLM 回复
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = reference # 默认使用RAG的引用

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref: # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content

    # 5. 写入 AI 回复到数据库
    _, ai_err = database.add_message_db(session_id, "ai", final_answer)
    if ai_err:
        print(f"Error writing AI message to DB: {ai_err}")
    
    return jsonify({"answer": final_answer, "reference": final_reference})

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

# AI chat 的 general 模式
@app.route('/api/aichat/general', methods=['POST'])
def aichat_general():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    # 保存用户消息到数据库
    database.add_message_db(session_id, 'user', question)
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
                "content": f"Question: {question}\n\n"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    # 4. 解析 LLM 回复
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref: # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content



    # 在这一部分加上 真实 ai 会话的逻辑 vvvv
    time.sleep(random.uniform(0.5, 1.5))  # 模拟AI延迟
    ai_reply = final_answer 
    # 在这一部分加上 真实 ai 会话的逻辑 ^^^^

    
    # 保存 AI 回复到数据库
    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({"answer": ai_reply})

# AI chat 的 rag 模式
@app.route('/api/aichat/rag', methods=['POST'])
def aichat_rag():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question)

    
    # 在这一部分加上 真实 ai 会话的逻辑 vvvv
    time.sleep(random.uniform(0.5, 1.5))
    pdf_title = "Account Disabled - CSE taggi.pdf"
    pdf_url = f"http://localhost:8000/pdfs/{pdf_title.replace(' ', '%20')}"
    ai_reply = f"[RAG] This is a mock RAG reply: {question}"
    # 在这一部分加上 真实 ai 会话的逻辑 ^^^^

    
    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({
        "answer": ai_reply,
        "reference": {pdf_title: pdf_url}
    })

# AI chat 的 checklist 模式
@app.route('/api/aichat/checklist', methods=['POST'])
def aichat_checklist():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question)
    knowledge, reference = rag_search(question)
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AI assistance called 'HDingo's AI chat bot', an AI designed to help new faculty, staff, and "
                    "students in the School of Computer Science and Engineering (CSE) complete their onboarding tasks.\n"
                    "Objectives:\n"
                    "1. Answer questions quickly and accurately about onboarding processes, policies, resources, and systems.\n"
                    "2. Cite the newest audited docs for consistency and authority.\n"
                    "3. If unclear/out of scope, guide user to submit an IT ticket or contact dept.\n"
                    "4. Style: professional, concise, friendly, easy to understand, and *in English*.\n"
                    "5. When answering procedural or instructional questions, provide a checklist starting with numbered steps "
                    "like '1.', '2.', '3.', etc., each describing a clear and actionable task.\n\n"
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
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    # 4. 解析 LLM 回复
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = reference # 默认使用RAG的引用

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref: # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content

    # 在这一部分加上 真实 ai 会话的逻辑 vvvv
    time.sleep(random.uniform(0.5, 1.5))
    checklist = [
        {"item": "Step 1: Do something", "done": False},
        {"item": "Step 2: Do something else", "done": False},
        {"item": "Step 3: Finish up", "done": False}
    ]
    ai_reply = final_answer 
    # 在这一部分加上 真实 ai 会话的逻辑 ^^^^

    
    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({"answer": ai_reply, "checklist": checklist})

@app.route('/api/update_session_title', methods=['POST'])
def update_session_title():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    title = data.get('title')
    if not session_id or not title:
        return jsonify({'success': False, 'error': 'session_id and title required'}), 400
    ok, err = database.update_session_title(session_id, title)
    if ok:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': err}), 500

@app.route('/api/delete_session', methods=['POST'])
def delete_session():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    ok, err = database.delete_session(session_id)
    if ok:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': err}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
