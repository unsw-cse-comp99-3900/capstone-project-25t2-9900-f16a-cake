from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from flask_mail import Mail, Message
import database  # database.py
from search import extract_keywords, multi_hot_encode, calculate_similarity
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

# 配置文件路径
CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果文件不存在，创建默认配置
        default_config = {"layout": "old"}
        save_config(default_config)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

list_pdf = []  # 公用pdf列表

app = Flask(__name__)
CORS(app)

# 邮件配置 - Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # 使用Gmail SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hdingo9900@gmail.com'  # 系统邮箱
app.config['MAIL_PASSWORD'] = 'gflf gpux rqdi sbkh'     # 系统邮箱应用密码
app.config['MAIL_DEFAULT_SENDER'] = 'hdingo9900@gmail.com'

mail = Mail(app)

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
        
        # 记录用户登录（排除admin用户）
        if db_role != "admin":
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            database.record_user_login(username, ip_address, user_agent)
        
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

    # 从数据库获取文档
    documents, error = database.get_pdf_documents_for_search()
    if error:
        return jsonify({"success": False, "error": error}), 500

    extracted = extract_keywords(query)
    query_encoded = multi_hot_encode(extracted)

    results = []
    for doc in documents:
        # 解析JSON格式的keywords_encoded
        try:
            keywords_encoded = json.loads(doc["keywords_encoded"])
        except:
            continue
            
        score = calculate_similarity(query_encoded, keywords_encoded, query, doc["title"])
        results.append({
            "title": doc["title"],
            "pdf_path": doc.get("pdf_path", ""),
            "score": score,
            "year": doc.get("year", "")
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
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400

    # 2. 获取表单数据
    title = request.form.get('title', '').strip()
    keywords = request.form.get('keywords', '').strip()
    year = request.form.get('year', '').strip()
    
    if not title:
        return jsonify({'success': False, 'message': 'Title is required'}), 400
    if not keywords:
        return jsonify({'success': False, 'message': 'Keywords are required'}), 400

    # 3. 保存 PDF
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)
    file_size = os.path.getsize(pdf_path)

    # 4. 生成关键词编码
    from search import multi_hot_encode
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    keywords_encoded = multi_hot_encode(keyword_list)
    keywords_encoded_json = json.dumps(keywords_encoded)

    # 5. 解析 PDF，生成问答对
    docs = build_docs_from_pdf(
        pdf_path=pdf_path,
        title=title,
        url=None,
        last_edited=None
    )

    # 6. 准备 texts 并生成 embeddings
    texts = [d['question'] + ' ' + d['answer'] for d in docs]
    if not texts:
        return jsonify({
            'success': False,
            'message': 'No Q&A pairs found in the PDF. Please check the file content.'
        }), 400

    embeddings = ragMODEL.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )
    emb_array = np.array(embeddings, dtype='float32')
    if emb_array.ndim == 1:
        emb_array = np.vstack(emb_array)

    # 7. 构建 FAISS 索引
    dim = emb_array.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(emb_array)

    # 8. 写入磁盘
    base = os.path.splitext(filename)[0]
    index_file = os.path.join(RAG_FOLDER, f"{base}.index")
    faiss.write_index(index, index_file)

    docs_file = os.path.join(RAG_FOLDER, f"{base}_docs.json")
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    ids_file = os.path.join(RAG_FOLDER, f"{base}_ids.pkl")
    ids = [d['id'] for d in docs]
    with open(ids_file, 'wb') as f:
        pickle.dump(ids, f)

    # 9. 保存到数据库
    uploader_id = None  # 可以从token中获取，暂时设为None
    success, error = database.save_pdf_document(
        title, keywords, keywords_encoded_json, filename, year, uploader_id, file_size
    )
    
    if not success:
        return jsonify({
            'success': False,
            'message': f'Failed to save document metadata: {error}'
        }), 500

    # 10. 更新关键词数据库并重新编码所有文档
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    success, msg = database.add_keywords_to_db(keyword_list)
    if not success:
        print(f"Warning: Failed to add keywords to database: {msg}")
    
    # 重新编码所有文档
    success, msg = database.update_all_documents_encoding()
    if not success:
        print(f"Warning: Failed to update document encodings: {msg}")

    # 11. 返回结果
    return jsonify({
        'success': True,
        'message': 'Upload succeeded, new RAG files have been generated',
        'pdf': filename,
        'title': title,
        'index_path': index_file,
        'docs_path': docs_file,
        'entries': len(docs)
    }), 200



# 获取所有pdf文件
@app.route('/api/admin/getpdfs', methods=['GET'])
def list_pdfs():
    documents, error = database.get_all_pdf_documents()
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    pdfs = []
    for doc in documents:
        pdfs.append({
            'id': doc['id'],
            'filename': doc['pdf_path'],
            'title': doc['title'],
            'keywords': doc['keywords'],
            'year': doc['year'],
            'size': doc['file_size'],
            'upload_time': doc['upload_time'].isoformat() if doc['upload_time'] else None
        })
    return jsonify({'success': True, 'pdfs': pdfs})


# 删除指定pdf文件
@app.route('/api/admin/deletepdf/<int:document_id>', methods=['DELETE'])
def delete_pdf(document_id):
    # 1. 从数据库获取文档信息
    documents, error = database.get_all_pdf_documents()
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    target_doc = None
    for doc in documents:
        if doc['id'] == document_id:
            target_doc = doc
            break
    
    if not target_doc:
        return jsonify({'success': False, 'error': 'Document not found'}), 404
    
    # 2. 删除物理PDF文件
    pdf_dir = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(pdf_dir, target_doc['pdf_path'])
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to delete PDF file: {str(e)}'}), 500
    
    # 3. 删除相关的RAG文件
    base = os.path.splitext(target_doc['pdf_path'])[0]
    rag_files = [
        os.path.join(RAG_FOLDER, f"{base}.index"),
        os.path.join(RAG_FOLDER, f"{base}_docs.json"),
        os.path.join(RAG_FOLDER, f"{base}_ids.pkl")
    ]
    
    for rag_file in rag_files:
        if os.path.isfile(rag_file):
            try:
                os.remove(rag_file)
                print(f"Deleted RAG file: {rag_file}")
            except Exception as e:
                print(f"Warning: Failed to delete RAG file {rag_file}: {str(e)}")
    
    # 4. 删除数据库记录
    success, error = database.delete_pdf_document(document_id)
    if not success:
        return jsonify({'success': False, 'error': f'Failed to delete database record: {error}'}), 500
    
    # 5. 更新关键词数据库并重新编码所有文档
    # 重新构建关键词数据库（从剩余文档中提取）
    success, msg = database.rebuild_keywords_database()
    if not success:
        print(f"Warning: Failed to rebuild keywords database: {msg}")
    
    # 重新编码所有文档
    success, msg = database.update_all_documents_encoding()
    if not success:
        print(f"Warning: Failed to update document encodings: {msg}")
    
    return jsonify({'success': True, 'message': 'PDF and related RAG files deleted successfully'})


@app.route('/api/aichat/general', methods=['POST'])
def aichat_general():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    
    # 保存用户消息到数据库
    database.add_message_db(session_id, 'user', question, mode='general')
    
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
    final_reference = {}
    need_human = False
    
    if data_json is not None:
        final_answer = data_json.get("answer", "")
        final_reference = data_json.get("reference", {})
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content
        # 如果解析失败，可能需要人工介入
        need_human = True

    ai_reply = final_answer
    reference_str = json.dumps(final_reference) if final_reference else None

    # 保存 AI 回复到数据库，包含参考资料和模式信息
    database.add_message_db(session_id, 'ai', ai_reply, 
                           reference=reference_str, 
                           mode='general',
                           need_human=need_human)
    
    return jsonify({"answer": ai_reply})


# AI chat 的 rag 模式
@app.route('/api/aichat/rag', methods=['POST'])
def aichat_rag():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    
    # 保存用户消息到数据库
    database.add_message_db(session_id, 'user', question, mode='rag')

    result = rag_search(question)

    # 如果 rag_search 返回 {}，表示没有需要的结果
    if not result:
        # 没有找到相关资料时，标记为需要人工介入
        database.add_message_db(session_id, 'ai', 
                               "ops, I couldn't find anything, Need I turn to real human?",
                               mode='rag',
                               need_human=True)
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

    final_answer = ""
    final_reference = reference  # 默认使用RAG的引用
    need_human = False

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content
        # 如果解析失败，可能需要人工介入
        need_human = True
    
    ai_reply = final_answer
    reference_str = json.dumps(final_reference) if final_reference else None
    print(reference)

    # 保存 AI 回复到数据库，包含参考资料
    database.add_message_db(session_id, 'ai', ai_reply,
                           reference=reference_str,
                           mode='rag',
                           need_human=need_human)
    
    return jsonify({
        "answer": ai_reply,
        "reference": final_reference
    })

from typing import Dict, Any, List

def parse_checklist_to_items(text: str) -> Dict[str, Any]:
    """
    将形如
      "Here’s a checklist to access your CSE files from your own computer: step1. … step2. …"
    的文本解析为：
    {
      "answer": "Here’s a checklist to access your CSE files from your own computer",
      "checklist": [
         {"item": "Step 1: …", "done": False},
         {"item": "Step 2: …", "done": False},
         ...
      ]
    }
    """
    # 1. 提取 answer（第一个冒号之前的内容）
    prefix, _, rest = text.partition(':')
    answer = prefix.strip()

    # 2. 按 stepX. 分块
    chunks = re.split(r'(?=(?:step\d+)\.)', rest)

    items: List[Dict[str, Any]] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # 匹配 stepX. 以及后面的描述
        m = re.match(r'step(\d+)\.\s*(.*)', chunk, flags=re.DOTALL)
        if m:
            idx = int(m.group(1))
            desc = m.group(2).strip()
            # 构造 “Step {idx}: {desc}”
            item_text = f"Step {idx}: {desc}"
            items.append({"item": item_text, "done": False})

    return {
        "answer": answer,
        "checklist": items
    }
# AI chat 的 checklist 模式
@app.route('/api/aichat/checklist', methods=['POST'])
def aichat_checklist():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    
    # 保存用户消息到数据库
    database.add_message_db(session_id, 'user', question, mode='checklist')
    
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
    need_human = False

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # 如果模型返回了引用，就用模型的
            final_reference = model_ref
    else:
        # Fallback: 如果模型没按 JSON 格式返回，直接使用其内容作为答案
        final_answer = content
        # 如果解析失败，可能需要人工介入
        need_human = True

    # 3. 调用解析函数
    result = parse_checklist_to_items(final_answer)

    # 4. 拆包到 ai_reply 和 checklist
    ai_reply = result["answer"]
    checklist = result["checklist"]
    
    # 将checklist转换为JSON字符串存储
    checklist_str = json.dumps(checklist) if checklist else None
    reference_str = json.dumps(final_reference) if final_reference else None
    
    # 保存 AI 回复到数据库，包含checklist
    database.add_message_db(session_id, 'ai', ai_reply,
                           reference=reference_str,
                           checklist=checklist_str,
                           mode='checklist',
                           need_human=need_human)
    
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
    # 获取真实的用户登录统计数据
    stats, error = database.get_daily_login_stats(7)
    if error:
        return jsonify({
            "success": False,
            "message": f"Failed to get user engagement data: {error}"
        }), 500
    
    return jsonify({
        "success": True,
        "data": stats
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
        
        # 获取所有admin邮箱
        admins, err = database.get_all_admins()
        if err:
            print(f"Error getting admin emails: {err}")
            return jsonify({
                "success": False,
                "message": "Failed to get admin emails"
            }), 500
        
        if not admins:
            print("No admin users found")
            return jsonify({
                "success": False,
                "message": "No admin users found"
            }), 500
        
        # 发送邮件给所有admin
        admin_emails = [admin['email'] for admin in admins]
        
        # 构建邮件内容
        subject = f"[HDingo Feedback] {feedback_data['subject']}"
        
        # 邮件正文
        body = f"""
New feedback received from HDingo system:

From: {feedback_data['name']} ({feedback_data['email']})
Category: {feedback_data['category']}
Subject: {feedback_data['subject']}
Rating: {feedback_data['rating']}/5
Allow Contact: {'Yes' if feedback_data['allow_contact'] else 'No'}

Description:
{feedback_data['description']}

---
This email was sent automatically by HDingo system.
Timestamp: {feedback_data['timestamp']}
        """.strip()
        
        try:
            # 发送邮件
            msg = Message(
                subject=subject,
                recipients=admin_emails,
                body=body
            )
            mail.send(msg)
            
            print(f"Feedback email sent successfully to {len(admin_emails)} admins:")
            for email in admin_emails:
                print(f"  - {email}")
            
            return jsonify({
                "success": True,
                "message": "Feedback submitted and sent to admins successfully"
            })
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Feedback submitted but failed to send email to admins"
            }), 500
        
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

# ==================== 新增的消息管理API ====================

@app.route('/api/admin/messages/need-human', methods=['GET'])
def get_messages_need_human_api():
    """获取所有需要人工介入的消息"""
    # 这里可以添加管理员权限验证
    messages, error = database.get_messages_need_human()
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    return jsonify({
        'success': True, 
        'messages': messages,
        'count': len(messages)
    })


@app.route('/api/admin/messages/stats', methods=['GET'])
def get_message_stats_api():
    """获取消息统计信息"""
    stats, error = database.get_message_stats_by_mode()
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@app.route('/api/admin/messages/by-mode/<mode>', methods=['GET'])
def get_messages_by_mode_api(mode):
    """根据模式获取消息"""
    if mode not in ['general', 'rag', 'checklist', 'human_ticket']:
        return jsonify({'success': False, 'error': 'Invalid mode'}), 400
    
    limit = request.args.get('limit', 100, type=int)
    messages, error = database.get_messages_by_mode(mode, limit)
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    return jsonify({
        'success': True,
        'messages': messages,
        'count': len(messages)
    })


@app.route('/api/admin/message/<int:message_id>/mark-human', methods=['POST'])
def mark_message_human_api(message_id):
    """标记消息需要人工介入"""
    data = request.get_json() or {}
    need_human = data.get('need_human', True)
    
    success, error = database.mark_message_need_human(message_id, need_human)
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    if not success:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
    
    return jsonify({
        'success': True,
        'message': f'Message {"marked as" if need_human else "unmarked from"} needing human intervention'
    })


@app.route('/api/admin/message/<int:message_id>/update-reference', methods=['POST'])
def update_message_reference_api(message_id):
    """更新消息的参考资料"""
    data = request.get_json() or {}
    reference = data.get('reference', '')
    
    success, error = database.update_message_reference(message_id, reference)
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    if not success:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
    
    return jsonify({
        'success': True,
        'message': 'Message reference updated successfully'
    })


@app.route('/api/admin/message/<int:message_id>/update-checklist', methods=['POST'])
def update_message_checklist_api(message_id):
    """更新消息的检查清单"""
    data = request.get_json() or {}
    checklist = data.get('checklist', [])
    
    # 将checklist转换为JSON字符串
    checklist_str = json.dumps(checklist) if checklist else None
    
    success, error = database.update_message_checklist(message_id, checklist_str)
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    if not success:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
    
    return jsonify({
        'success': True,
        'message': 'Message checklist updated successfully'
    })


@app.route('/api/message/<int:message_id>/details', methods=['GET'])
def get_message_details_api(message_id):
    """获取单个消息的详细信息"""
    conn = database.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT m.*, ch.user_id, ch.title as session_title, "
            "ui.first_name, ui.last_name, ui.email "
            "FROM messages m "
            "JOIN chat_history ch ON m.session_id = ch.session_id "
            "JOIN user_info ui ON ch.user_id = ui.user_id "
            "WHERE m.message_id = %s",
            (message_id,)
        )
        message = cursor.fetchone()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        
        # 处理布尔值转换和JSON解析
        message['need_human'] = bool(message['need_human'])
        if message['checklist']:
            try:
                message['checklist'] = json.loads(message['checklist'])
            except json.JSONDecodeError:
                message['checklist'] = None
        
        if message['reference']:
            try:
                message['reference'] = json.loads(message['reference'])
            except json.JSONDecodeError:
                pass  # 保持原始字符串
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# ==================== 转人工工单系统API ====================

@app.route('/api/save_ticket', methods=['POST'])
def save_ticket_api():
    """保存转人工请求工单"""
    # 从请求头获取token进行身份验证
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
        staff_id = payload.get('username') or payload.get('id')
        
        if not staff_id:
            return jsonify({
                "success": False,
                "message": "Invalid token: missing user ID"
            }), 401
        
        # 从数据库获取用户详细信息
        user = database.get_user(staff_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['session_id', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        session_id = data.get('session_id')
        content = data.get('content')
        staff_email = user.get('email', '')
        
        # 保存工单到数据库
        ticket_id, error = database.save_ticket(session_id, staff_id, staff_email, content)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to save ticket: {error}"
            }), 500
        
        # 发送邮件通知管理员（可选）
        try:
            admins, err = database.get_all_admins()
            if not err and admins:
                admin_emails = [admin['email'] for admin in admins]
                
                subject = f"[HDingo] New Human Support Request - Ticket #{ticket_id}"
                body = f"""
New human support request received:

Ticket ID: {ticket_id}
From: {user.get('first_name', '')} {user.get('last_name', '')} ({staff_email})
Department: {user.get('department', 'N/A')}
Role: {user.get('role', 'N/A')}
Session ID: {session_id}

Request Content:
{content}

Please log in to the admin panel to review and process this request.

---
This email was sent automatically by HDingo system.
Time: {datetime.now().isoformat()}
                """.strip()
                
                msg = Message(
                    subject=subject,
                    recipients=admin_emails,
                    body=body
                )
                mail.send(msg)
                print(f"Notification email sent to {len(admin_emails)} admins for ticket #{ticket_id}")
        except Exception as e:
            print(f"Warning: Failed to send notification email for ticket #{ticket_id}: {str(e)}")
        
        return jsonify({
            "success": True,
            "message": "Ticket created successfully",
            "ticket_id": ticket_id
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


@app.route('/api/get_tickets', methods=['GET'])
def get_tickets_api():
    """获取工单列表"""
    # 从请求头获取token进行管理员权限验证
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
        user_role = payload.get('role')
        
        # 检查是否是管理员
        if user_role != 'admin':
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        # 获取查询参数
        show_all = request.args.get('all', 'false').lower() == 'true'
        limit = request.args.get('limit', 100, type=int)
        
        if show_all:
            tickets, error = database.get_all_tickets(limit)
        else:
            tickets, error = database.get_unfinished_tickets(limit)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to get tickets: {error}"
            }), 500
        
        return jsonify({
            "success": True,
            "tickets": tickets,
            "count": len(tickets)
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


@app.route('/api/finish_ticket', methods=['POST'])
def finish_ticket_api():
    """完成工单处理"""
    # 从请求头获取token进行管理员权限验证
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
        user_role = payload.get('role')
        
        # 检查是否是管理员
        if user_role != 'admin':
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('ticket_id'):
            return jsonify({
                "success": False,
                "message": "Missing required field: ticket_id"
            }), 400
        
        ticket_id = data.get('ticket_id')
        admin_notes = data.get('admin_notes', '')
        
        # 更新工单状态
        success, error = database.finish_ticket(ticket_id, admin_notes)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to finish ticket: {error}"
            }), 500
        
        if not success:
            return jsonify({
                "success": False,
                "message": "Ticket not found"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Ticket marked as finished successfully"
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


@app.route('/api/tickets/stats', methods=['GET'])
def get_tickets_stats_api():
    """获取工单统计信息"""
    # 从请求头获取token进行管理员权限验证
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
        user_role = payload.get('role')
        
        # 检查是否是管理员
        if user_role != 'admin':
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        stats, error = database.get_tickets_stats()
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to get tickets stats: {error}"
            }), 500
        
        return jsonify({
            "success": True,
            "stats": stats
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


@app.route('/api/ticket/<int:ticket_id>', methods=['GET'])
def get_ticket_details_api(ticket_id):
    """获取单个工单详情"""
    # 从请求头获取token进行权限验证
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
        user_role = payload.get('role')
        user_id = payload.get('username') or payload.get('id')
        
        # 获取工单详情
        ticket, error = database.get_ticket_by_id(ticket_id)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to get ticket details: {error}"
            }), 500
        
        if not ticket:
            return jsonify({
                "success": False,
                "message": "Ticket not found"
            }), 404
        
        # 权限检查：管理员可以查看所有工单，普通用户只能查看自己的工单
        if user_role != 'admin' and ticket['staff_id'] != user_id:
            return jsonify({
                "success": False,
                "message": "Access denied: You can only view your own tickets"
            }), 403
        
        return jsonify({
            "success": True,
            "ticket": ticket
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


@app.route('/api/my_tickets', methods=['GET'])
def get_my_tickets_api():
    """获取当前用户的工单列表"""
    # 从请求头获取token进行身份验证
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
        staff_id = payload.get('username') or payload.get('id')
        
        if not staff_id:
            return jsonify({
                "success": False,
                "message": "Invalid token: missing user ID"
            }), 401
        
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        
        tickets, error = database.get_tickets_by_staff(staff_id, limit)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to get tickets: {error}"
            }), 500
        
        return jsonify({
            "success": True,
            "tickets": tickets,
            "count": len(tickets)
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

# 新版 旧版 布局的切换和保存
@app.route('/api/readconfig', methods=['GET'])
def read_config():
    config = load_config()
    return jsonify(config)

@app.route('/api/updateconfig', methods=['POST'])
def update_config():
    data = request.get_json()
    if not data or 'layout' not in data:
        return jsonify({'error': 'layout field is required'}), 400
    
    if data['layout'] not in ['new', 'old']:
        return jsonify({'error': 'layout must be "new" or "old"'}), 400
    
    config = load_config()
    config['layout'] = data['layout']
    save_config(config)
    
    return jsonify({'success': True, 'config': config})


# mock ai chat api for frontend development

mockmd = """---
__Advertisement :)__

- __[pica](https://nodeca.github.io/pica/demo/)__ - high quality and fast image
  resize in browser.
- __[babelfish](https://github.com/nodeca/babelfish/)__ - developer friendly
  i18n with plurals support and easy syntax.

You will like those projects!

---

# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading


## Horizontal Rules

___

---

***


## Typographic replacements

Enable typographer option to see result.

(c) (C) (r) (R) (tm) (TM) (p) (P) +-

test.. test... test..... test?..... test!....

!!!!!! ???? ,,  -- ---

"Smartypants, double quotes" and 'single quotes'


## Emphasis

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~


## Blockquotes


> Blockquotes can also be nested...
>> ...by using additional greater-than signs right next to each other...
> > > ...or with spaces between arrows.


## Lists

Unordered

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!

Ordered

1. Lorem ipsum dolor sit amet
2. Consectetur adipiscing elit
3. Integer molestie lorem at massa


1. You can use sequential numbers...
1. ...or keep all the numbers as `1.`

Start numbering with offset:

57. foo
1. bar


## Code

Inline `code`

Indented code

    // Some comments
    line 1 of code
    line 2 of code
    line 3 of code


Block code "fences"

```
Sample text here...
```

Syntax highlighting

``` js
var foo = function (bar) {
  return bar++;
};

console.log(foo(5));
```

## Tables

| Option | Description |
| ------ | ----------- |
| data   | path to data files to supply the data that will be passed into templates. |
| engine | engine to be used for processing templates. Handlebars is the default. |
| ext    | extension to be used for dest files. |

Right aligned columns

| Option | Description |
| ------:| -----------:|
| data   | path to data files to supply the data that will be passed into templates. |
| engine | engine to be used for processing templates. Handlebars is the default. |
| ext    | extension to be used for dest files. |


## Links

[link text](http://dev.nodeca.com)

[link with title](http://nodeca.github.io/pica/demo/ "title text!")

Autoconverted link https://github.com/nodeca/pica (enable linkify to see)


## Images

![Minion](https://octodex.github.com/images/minion.png)
![Stormtroopocat](https://octodex.github.com/images/stormtroopocat.jpg "The Stormtroopocat")

Like links, Images also have a footnote style syntax

![Alt text][id]

With a reference later in the document defining the URL location:

[id]: https://octodex.github.com/images/dojocat.jpg  "The Dojocat"


## Plugins

The killer feature of `markdown-it` is very effective support of
[syntax plugins](https://www.npmjs.org/browse/keyword/markdown-it-plugin).


### [Emojies](https://github.com/markdown-it/markdown-it-emoji)

> Classic markup: :wink: :cry: :laughing: :yum:
>
> Shortcuts (emoticons): :-) :-( 8-) ;)

see [how to change output](https://github.com/markdown-it/markdown-it-emoji#change-output) with twemoji.


### [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)

- 19^th^
- H~2~O


### [\<ins>](https://github.com/markdown-it/markdown-it-ins)

++Inserted text++


### [\<mark>](https://github.com/markdown-it/markdown-it-mark)

==Marked text==


### [Footnotes](https://github.com/markdown-it/markdown-it-footnote)

Footnote 1 link[^first].

Footnote 2 link[^second].

Inline footnote^[Text of inline footnote] definition.

Duplicated footnote reference[^second].

[^first]: Footnote **can have markup**

    and multiple paragraphs.

[^second]: Footnote text.


### [Definition lists](https://github.com/markdown-it/markdown-it-deflist)

Term 1

:   Definition 1
with lazy continuation.

Term 2 with *inline markup*

:   Definition 2

        { some code, part of Definition 2 }

    Third paragraph of definition 2.

_Compact style:_

Term 1
  ~ Definition 1

Term 2
  ~ Definition 2a
  ~ Definition 2b


### [Abbreviations](https://github.com/markdown-it/markdown-it-abbr)

This is HTML abbreviation example.

It converts "HTML", but keep intact partial entries like "xxxHTMLyyy" and so on.

*[HTML]: Hyper Text Markup Language

### [Custom containers](https://github.com/markdown-it/markdown-it-container)

::: warning
*here be dragons*
:::
"""

@app.route('/api/aichat/mock/general', methods=['POST'])
def aichat_general_mock():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    # 保存用户消息到数据库
    database.add_message_db(session_id, 'user', question)

    ai_reply = mockmd

    # 保存 AI 回复到数据库
    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({
        "answer": ai_reply,
        "reference": [],
        "checklist": [],
        "mode": "general",
        "need_human": False
    })


@app.route('/api/aichat/mock/rag', methods=['POST'])
def aichat_rag_mock():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question)

    ai_reply = "There is no reference for this RAG question.  \n\nYou can press the button below to ask for human help."

    database.add_message_db(session_id, 'ai', ai_reply)

    need = False

    if need:
        return jsonify({
            "answer": ai_reply,
            "reference": [],
            "checklist": [],
            "mode": "rag",
            "need_human": True
        })
    else:
        return jsonify({
            "answer": mockmd,
            "reference": {
                "Account Disabled - CSE taggi.pdf": "http://localhost:8000/pdfs/Account_Disabled_-_CSE_taggi.pdf",
                "Account expiry - CSE taggi.pdf": "http://localhost:8000/pdfs/Account_expiry_-_CSE_taggi.pdf"
            },
            "checklist": [],
            "mode": "rag",
            "need_human": False
        })

@app.route('/api/aichat/mock/checklist', methods=['POST'])
def aichat_checklist_mock():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question)

    ai_reply = "There is no reference for this checklist question.  \n\nYou can press the button below to ask for human help."

    database.add_message_db(session_id, 'ai', ai_reply)
    return jsonify({
        "answer": ai_reply,
        "reference": [],
        "checklist": [],
        "mode": "checklist",
        "need_human": True
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
