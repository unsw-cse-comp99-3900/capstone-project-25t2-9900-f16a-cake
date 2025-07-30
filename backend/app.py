from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
import database  # database.py
from search import extract_keywords, multi_hot_encode, calculate_similarity, DATABASE
import requests
# v 生成 token 的库 v
import jwt
import datetime  # 用于 JWT 过期时间等
# ^ 生成 token 的库 ^

# ————————生成rag————————
import re
import uuid
import logging
import pdfplumber
from werkzeug.utils import secure_filename

# —————————rag———————————
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime  # 用于文件时间展示
import time
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

list_pdf = []  # 公用pdf列表

app = Flask(__name__)
CORS(app)

# 上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
RAG_FOLDER = os.path.join(os.path.dirname(__file__), 'rag')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RAG_FOLDER, exist_ok=True)

# RAG 模型初始化
ragMODEL = SentenceTransformer('all-MiniLM-L6-v2')
PDF_URL_BASE = "http://localhost:8000/pdfs"

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
def list_pdf_names(pdfs_dir="pdfs"):
    """
    返回指定目录下所有 .pdf 文件的文件名。
    """
    try:
        files = os.listdir(pdfs_dir)
    except FileNotFoundError:
        # 如果目录不存在，返回空列表
        return []
    pdf_names = []
    for f in files:
        # 忽略隐藏文件和非 .pdf 文件
        if not f.lower().endswith(".pdf"):
            continue
        name, _ = os.path.splitext(f)
        pdf_names.append(name)
    return pdf_names


def rag_search(question, top_k=10, score_threshold=0.85):
    # 1. 先拿到所有 PDF 的前缀名
    pdf_list = list_pdf_names()

    # 2. 生成 query 向量
    model = SentenceTransformer("all-MiniLM-L6-v2")
    q_emb = model.encode([question])

    all_hits = []
    for prefix in pdf_list:
        # 3. 构造索引 & 元数据路径
        idx_path = os.path.join(BASE_DIR, "rag", f"{prefix}.index")
        ids_path = os.path.join(BASE_DIR, "rag", f"{prefix}_ids.pkl")
        docs_path = os.path.join(BASE_DIR, "rag", f"{prefix}_docs.json")

        # 如果没有对应文件就跳过
        if not (os.path.exists(idx_path) and os.path.exists(ids_path) and os.path.exists(docs_path)):
            continue

        # 4. 加载索引和文档映射
        index = faiss.read_index(idx_path)
        with open(ids_path, "rb") as f:
            ids = pickle.load(f)
        with open(docs_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        doc_map = {d["id"]: d for d in docs}

        # 5. 检索 top_k
        D, I = index.search(np.array(q_emb, dtype="float32"), top_k)
        for dist, idx in zip(D[0], I[0]):
            if dist > score_threshold:
                continue
            entry = doc_map[ids[idx]]
            all_hits.append({
                "score": float(dist),
                "pdf": prefix,
                "question": entry.get("question", ""),
                "answer": entry.get("answer", ""),
                # 改这里：title 直接用 prefix；url 用 pdfs 目录下的文件路径
                "title": prefix,
                "url": f"{PDF_URL_BASE}/{prefix}.pdf",
            })

    # 6. 全部合并后排序并取最终 top_k
    all_hits = sorted(all_hits, key=lambda x: x["score"])[:top_k]
    if not all_hits:
        return {}
    # 7. 组装返回值
    parts = []
    ref_dict = {}
    for h in all_hits:
        prefix = h["pdf"]
        url = h["url"]
        # 如果同一个 pdf 出现多次，这里会被后面的覆盖一次，最终得到唯一映射
        ref_dict[prefix] = url

    # 构造 knowledge_str 同之前
    parts = [
        f"{i}. （{h['pdf']}）Question: {h['question']}\n"
        f"   Answer:   {h['answer']}"
        for i, h in enumerate(all_hits, 1)
    ]
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
    ok, err = database.check_or_create_session(session_id, user_id,
                                               title=f"Chat on {datetime.now().strftime('%Y-%m-%d')}")
    if not ok:
        return jsonify({"error": f"Failed to ensure session exists: {err}"}), 500

    # 1. 写入用户提问到数据库
    _, user_err = database.add_message_db(session_id, user_role, question)
    if user_err:
        # 即使写入失败，也可以选择继续，但最好记录日志
        print(f"Error writing user message to DB: {user_err}")
    result = rag_search(question)
    # 如果 rag_search 返回 {}，表示没命中
    if not result:
        return jsonify({
            "answer": "ops, I couldn't find anything, Need I turn to real human?",
            "reference": {}
        })
    # 2. RAG 检索
    knowledge, reference = result
    print(knowledge)
    # 这里增加了如果找不到直接返回结果

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
    final_reference = reference  # 默认使用RAG的引用

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # 如果模型返回了引用，就用模型的
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


# ————————生成rag————————
def extract_text_from_pdf(path):
    """
    提取 PDF 中文本，并返回整个文档的字符串。
    """
    texts = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text()
            except Exception as e:
                logging.error(f"第{page_num}页提取文本时出错: {e}")
                continue
            if text:
                texts.append(text)
    return "\n".join(texts)


def parse_qa_pairs(full_text):
    """
    从全文中提取问答对。
    匹配问号结尾或数字标题行作为问题，后续内容作为答案。
    """
    docs = []
    lines = [line.strip() for line in full_text.splitlines()]
    heading_re = re.compile(r'^(\d+(?:\.\d+)*):\s*(.+)')
    i = 0
    while i < len(lines):
        question = None
        line = lines[i]
        if line.endswith('?') or line.endswith('？'):
            question = line
        else:
            m = heading_re.match(line)
            if m:
                question = m.group(2)
        if question:
            answer_lines = []
            j = i + 1
            while j < len(lines) and lines[j]:
                if lines[j].endswith('?') or heading_re.match(lines[j]):
                    break
                answer_lines.append(lines[j])
                j += 1
            answer = ' '.join(answer_lines).strip()
            docs.append({
                'id': f"qa_{uuid.uuid4().hex[:8]}",
                'question': question,
                'answer': answer
            })
            i = j
        else:
            i += 1
    return docs


def build_docs_from_pdf(pdf_path, title, url=None, last_edited=None):
    """
    从 PDF 构建问答文档列表。
    """
    text = extract_text_from_pdf(pdf_path)
    qa = parse_qa_pairs(text)
    docs = []
    for item in qa:
        docs.append({
            **item,
            'source': {
                'title': title,
                'url': url or pdf_path,
                'last_edited': last_edited or datetime.today().isoformat()
            }
        })
    return docs


@app.route('/api/upload', methods=['POST'])
def upload_and_generate_rag():
    # 1. 文件接收及验证
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '只允许上传 PDF 文件'}), 400

    # 2. 保存 PDF
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)

    # 3. 解析 PDF，生成问答对
    docs = build_docs_from_pdf(
        pdf_path=pdf_path,
        title=filename,
        url=None,
        last_edited=None
    )

    # 4. 针对本文件单独生成 embeddings 和 FAISS 索引
    texts = [d['question'] + ' ' + d['answer'] for d in docs]
    embeddings = ragMODEL.encode(texts, show_progress_bar=False)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings, dtype='float32'))

    # 5. 构造输出文件名
    base = os.path.splitext(filename)[0]
    index_file = os.path.join(RAG_FOLDER, f"{base}.index")
    docs_file = os.path.join(RAG_FOLDER, f"{base}_docs.json")
    ids_file = os.path.join(RAG_FOLDER, f"{base}_ids.pkl")

    # 6. 写入磁盘
    faiss.write_index(index, index_file)
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    # 7. 保存 ID 列表到 pkl
    ids = [d['id'] for d in docs]
    with open(ids_file, 'wb') as f:
        pickle.dump(ids, f)

    # 8. 返回结果
    return jsonify({
        'success': True,
        'message': '上传成功，已生成新的 RAG 文件',
        'pdf': filename,
        'index_path': index_file,
        'docs_path': docs_file,
        'entries': len(docs)
    }), 200


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

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content

    ai_reply = final_answer

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

    result = rag_search(question)

    # 如果 rag_search 返回 {}，表示没有需要的结果
    if not result:
        return jsonify({
            "answer": "ops, I couldn't find anything, Need I turn to real human?",
            "reference": {}
        })

    # 2. RAG 检索
    knowledge, reference = result

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

    if data_json is not None:
        ai_reply = data_json.get("answer", "")
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        ai_reply = content
    print(reference)

    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({
        "answer": ai_reply,
        "reference": reference
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
                    "like 'step1.', 'step2.', 'step3.', etc., each describing a clear and actionable task.\n\n"
                    "You must return ONLY valid JSON with two keys:\n"
                    "  - \"answer\": string (the final answer)\n"
                    "  - \"reference\": object (mapping title -> url of cited docs)\n"
                    "Do not include code fences. Do not include any additional keys."
                )
            },
            {
                "role": "user",
                "content": f"give me a checklist about Question: {question}\n\n Relevant knowledge:\n{knowledge}"
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
    final_reference = reference  # 默认使用RAG的引用

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content

    time.sleep(random.uniform(0.5, 1.5))
    checklist = [
    ]
    ai_reply = final_answer

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


@app.route('/api/user-engagement', methods=['GET'])
def get_user_engagement():
    # Mock data for user engagement over the last 7 days
    mock_data = [
        {"date": "2024-01-15", "active_users": 12},
        {"date": "2024-01-16", "active_users": 18},
        {"date": "2024-01-17", "active_users": 15},
        {"date": "2024-01-18", "active_users": 22},
        {"date": "2024-01-19", "active_users": 19},
        {"date": "2024-01-20", "active_users": 25},
        {"date": "2024-01-21", "active_users": 21}
    ]
    
    return jsonify({
        "success": True,
        "data": mock_data
    })


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    # 从请求头获取token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # 解码token获取用户信息
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('username')
        
        # 从数据库获取用户详细信息
        user = database.get_user(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['category', 'subject', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # 构建反馈数据，包含用户信息
        feedback_data = {
            "user_id": user_id,
            "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            "email": user.get('email'),
            "category": data.get('category'),
            "subject": data.get('subject'),
            "description": data.get('description'),
            "rating": data.get('rating', 0),
            "allow_contact": data.get('allowContact', False),
            "timestamp": datetime.now().isoformat()
        }
        
        # 打印反馈信息（开发时用于调试）
        print("New feedback received:")
        print(f"From: {feedback_data['name']} ({feedback_data['email']})")
        print(f"Category: {feedback_data['category']}")
        print(f"Subject: {feedback_data['subject']}")
        print(f"Rating: {feedback_data['rating']}/5")
        print(f"Description: {feedback_data['description']}")
        print(f"Allow contact: {feedback_data['allow_contact']}")
        print("-" * 50)
        
        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully"
        })
        
    except jwt.InvalidTokenError:
        return jsonify({
            "success": False,
            "message": "Invalid token"
        }), 401
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
