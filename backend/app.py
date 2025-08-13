"""
HDingo Backend Application
==========================

This is the main Flask backend application for the HDingo project, a comprehensive
AI-powered onboarding assistance system for the School of Computer Science and 
Engineering (CSE) at UNSW.

Project: Capstone Project 25T2-9900-F16A-CAKE
Team: HDingo
University: UNSW
Course: COMP9900

Features:
- User authentication and authorization (JWT-based)
- AI chat system with multiple modes (General, RAG, Checklist)
- PDF document management and RAG (Retrieval-Augmented Generation)
- Search functionality with keyword extraction and similarity matching
- Human support ticket system
- Email notifications
- User engagement tracking
- Admin dashboard and management tools

API Endpoints:
- Authentication: /api/login, /api/profile
- Chat: /api/ask, /api/aichat/*
- Document Management: /api/upload, /api/admin/*
- Search: /api/search
- Support: /api/save_ticket, /api/get_tickets
- Configuration: /api/readconfig, /api/updateconfig

Dependencies:
- Flask: Web framework
- Flask-CORS: Cross-origin resource sharing
- Flask-Mail: Email functionality
- JWT: JSON Web Token authentication
- FAISS: Vector similarity search
- SentenceTransformers: Text embeddings
- PDFPlumber: PDF text extraction

Author: HDingo Team
Last Updated: 2024
License: Internal UNSW Project
"""

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from flask_mail import Mail, Message
import database  # database.py
from search import extract_keywords, multi_hot_encode, calculate_similarity
import requests
# JWT token generation library
import jwt
import datetime  # For JWT expiration time, etc.
# JWT token generation library

# RAG (Retrieval-Augmented Generation) imports
import re
import uuid
import logging
import pdfplumber
from werkzeug.utils import secure_filename

# RAG (Retrieval-Augmented Generation) imports
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime  # For file time display
import time
import random
import os

# Configuration file path
CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # If file doesn't exist, create default configuration
        default_config = {"layout": "old"}
        save_config(default_config)
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

list_pdf = []  # Public PDF list

app = Flask(__name__)
CORS(app)

# Gmail SMTP config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hdingo9900@gmail.com'
app.config['MAIL_PASSWORD'] = 'gflf gpux rqdi sbkh'
app.config['MAIL_DEFAULT_SENDER'] = 'hdingo9900@gmail.com'

mail = Mail(app)

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
RAG_FOLDER = os.path.join(os.path.dirname(__file__), 'rag')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RAG_FOLDER, exist_ok=True)

# RAG model initialization
ragMODEL = SentenceTransformer('all-MiniLM-L6-v2')
PDF_URL_BASE = "http://localhost:8000/pdfs"

# AI Chat Configuration Section
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/QwQ-32B"
API_KEY = "sk-xlrowobsoqpeykasamsgwlbjiilruinjklvbryuvbiukhekt"

# Secret key for token generation
SECRET_KEY = "hdingo_secret_key"

# End of AI Chat Configuration

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
# Flask global parameter for storing uploaded file locations
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---- Test API ----
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")


# ---- Login API (Query database user_info) ----
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
        # Note: user_info table should have role field! Otherwise use identity/is_admin for judgment
        db_role = "admin" if user.get("is_admin") == 1 else "staff"
        if db_role != role:
            return jsonify({"success": False, "message": "Invalid role"}), 400
        
        # Record user login (exclude admin users)
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
            # "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # Optional
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


@app.route('/api/get_sessions/<user_id>', methods=['GET'])
def api_get_sessions(user_id):
    sessions, error = database.get_sessions_db(user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(sessions)


# ---- SSO Login Simulation ----
@app.route('/api/sso-login', methods=['GET'])
def sso_login():
    return jsonify({"success": True, "role": "staff", "message": "SSO Login success!"})


# ---- Search API ----
@app.route('/api/search', methods=['POST'])
def search_api():
    data = request.get_json()
    query = data.get("query", "").strip()

    # Get documents from database
    documents, error = database.get_pdf_documents_for_search()
    if error:
        return jsonify({"success": False, "error": error}), 500

    extracted = extract_keywords(query)
    query_encoded = multi_hot_encode(extracted)

    results = []
    for doc in documents:
        # Parse JSON format keywords_encoded
        try:
            keywords_encoded = json.loads(doc["keywords_encoded"])
        except:
            continue
            
        score = calculate_similarity(query_encoded, keywords_encoded, query, doc["title"])
        # Handle document_date format
        document_date = doc.get("document_date", "")
        if document_date and hasattr(document_date, 'isoformat'):
            # If it's a datetime object, convert to ISO format string
            document_date = document_date.isoformat()
        elif document_date:
            # If it's a string, keep as is
            document_date = str(document_date)
        
        results.append({
            "title": doc["title"],
            "pdf_path": doc.get("pdf_path", ""),
            "score": score,
            "document_date": document_date
        })

    # Set higher threshold, only return results with real matching degree
    filtered = sorted([r for r in results if r["score"] > 0.1], key=lambda x: x["score"], reverse=True)[:5]

    return jsonify({"results": filtered})


# ---- Get User Profile API ----
@app.route('/api/profile', methods=['GET'])
def get_profile():
    # 1. Get Authorization from request header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Authorization header is missing or invalid"}), 401

    # 2. Extract and decode JWT token
    token = auth_header.split(" ")[1]
    try:
        # Use SECRET_KEY defined at the top of the file for decoding
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Get user_id from token payload (we stored 'id' during login)
        user_id = payload.get('id')
        if not user_id:
            raise jwt.InvalidTokenError("Token payload is missing user ID")

    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Invalid token"}), 401

    # 3. Use user_id to query user information from database
    user_data = database.get_user(user_id)
    if not user_data:
        return jsonify({"success": False, "message": "User not found"}), 404

    # 4. Organize and return profile information (excluding sensitive info like password)
    profile_info = {
        "userId": user_data.get("user_id"),
        "firstName": user_data.get("first_name"),
        "lastName": user_data.get("last_name"),
        "email": user_data.get("email"),
        "phone": user_data.get("phone"),
        "department": user_data.get("department"),
        "role": user_data.get("role")  # This is the detailed role, such as 'PhD Student', 'Tutor'
    }

    return jsonify({"success": True, "profile": profile_info})


# ---- Homepage (Demo redirect only) ----
@app.route('/')
def home():
    return 'Welcome to the demo backend!'


# ---------------- RAG -----------------
def list_pdf_names(pdfs_dir="pdfs"):
    """
    Returns the filenames of all .pdf files in the specified directory.
    """
    try:
        files = os.listdir(pdfs_dir)
    except FileNotFoundError:
        # If directory doesn't exist, return empty list
        return []
    pdf_names = []
    for f in files:
        # Ignore hidden files and non-.pdf files
        if not f.lower().endswith(".pdf"):
            continue
        name, _ = os.path.splitext(f)
        pdf_names.append(name)
    return pdf_names


def rag_search(question, top_k=10, score_threshold=1.0):
    # 1. First get all PDF prefix names
    pdf_list = list_pdf_names()

    # 2. Generate query vector
    model = SentenceTransformer("all-MiniLM-L6-v2")
    q_emb = model.encode([question])

    all_hits = []
    for prefix in pdf_list:
        # 3. Construct index & metadata paths
        idx_path = os.path.join(BASE_DIR, "rag", f"{prefix}.index")
        ids_path = os.path.join(BASE_DIR, "rag", f"{prefix}_ids.pkl")
        docs_path = os.path.join(BASE_DIR, "rag", f"{prefix}_docs.json")

        # Skip if corresponding files don't exist
        if not (os.path.exists(idx_path) and os.path.exists(ids_path) and os.path.exists(docs_path)):
            continue

        # 4. Load index and document mapping
        index = faiss.read_index(idx_path)
        with open(ids_path, "rb") as f:
            ids = pickle.load(f)
        with open(docs_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        doc_map = {d["id"]: d for d in docs}

        # 5. Retrieve top_k
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
                # Change here: title directly uses prefix; url uses file path under pdfs directory
                "title": prefix,
                "url": f"{PDF_URL_BASE}/{prefix}.pdf",
            })

    # 6. Merge all, sort and take final top_k
    all_hits = sorted(all_hits, key=lambda x: x["score"])[:top_k]
    if not all_hits:
        return {}
    # 7. Assemble return value
    parts = []
    ref_dict = {}
    for h in all_hits:
        prefix = h["pdf"]
        url = h["url"]
        # If the same pdf appears multiple times, it will be overwritten once here, finally getting unique mapping
        ref_dict[prefix] = url

    # Construct knowledge_str same as before
    parts = [
        f"{i}. （{h['pdf']}）Question: {h['question']}\n"
        f"   Answer:   {h['answer']}"
        for i, h in enumerate(all_hits, 1)
    ]
    knowledge_str = "\n\n".join(parts)

    return knowledge_str, ref_dict


def try_load_json(text: str):
    """Prioritize parsing model output as JSON, return None and exception if failed"""
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, e


# ---- AI Chat API ----
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id', None)
    user_id = data.get('user_id', None)
    user_role = data.get('role', 'user')

    if not all([question, session_id, user_id]):
        return jsonify({"error": "question, session_id, and user_id are required"}), 400

    # Before writing message, check and create session history
    ok, err = database.check_or_create_session(session_id, user_id,
                                               title=f"Chat on {datetime.now().strftime('%Y-%m-%d')}")
    if not ok:
        return jsonify({"error": f"Failed to ensure session exists: {err}"}), 500

    # 1. Write user question to database
    _, user_err = database.add_message_db(session_id, user_role, question)
    if user_err:
        # Even if writing fails, we can choose to continue, but it's better to log
        print(f"Error writing user message to DB: {user_err}")
    result = rag_search(question)
    # If rag_search returns {}, it means no match
    if not result:
        return jsonify({
            "answer": "ops, I couldn't find anything, Need I turn to real human?",
            "reference": {}
        })
    # 2. RAG retrieval
    knowledge, reference = result
    print(knowledge)
    # Added here: if nothing found, return result directly

    # 3. Construct and request LLM
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

    # 4. Parse LLM response
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = reference  # Default to using RAG reference

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # If model returns reference, use model's
            final_reference = model_ref
    else:
        # Fallback: If model doesn't return in JSON format, use content directly as answer
        final_answer = content

    # 5. Write AI response to database
    _, ai_err = database.add_message_db(session_id, "ai", final_answer)
    if ai_err:
        print(f"Error writing AI message to DB: {ai_err}")

    return jsonify({"answer": final_answer, "reference": final_reference})


@app.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('pdfs', filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# RAG Generation
def extract_text_from_pdf(path):
    """
    Extract text from PDF and return the entire document as a string.
    """
    texts = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text()
            except Exception as e:
                logging.error(f"Error extracting text from page {page_num}: {e}")
                continue
            if text:
                texts.append(text)
    return "\n".join(texts)


def parse_qa_pairs(full_text):
    """
    Extract Q&A pairs from full text.
    Match lines ending with question marks or numbered heading lines as questions, 
    with subsequent content as answers.
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
    Build Q&A document list from PDF.
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
    # 1. File reception and validation
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400

    # 2. Get form data
    title = request.form.get('title', '').strip()
    keywords = request.form.get('keywords', '').strip()
    document_date = request.form.get('document_date', '').strip()
    
    if not title:
        return jsonify({'success': False, 'message': 'Title is required'}), 400
    if not keywords:
        return jsonify({'success': False, 'message': 'Keywords are required'}), 400

    # 3. Save PDF
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(pdf_path)
    file_size = os.path.getsize(pdf_path)

    # 4. Generate keyword encoding
    from search import multi_hot_encode
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    keywords_encoded = multi_hot_encode(keyword_list)
    keywords_encoded_json = json.dumps(keywords_encoded)

    # 5. Parse PDF, generate Q&A pairs
    docs = build_docs_from_pdf(
        pdf_path=pdf_path,
        title=title,
        url=None,
        last_edited=None
    )

    # 6. Prepare texts and generate embeddings
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

    # 7. Build FAISS index
    dim = emb_array.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(emb_array)

    # 8. Write to disk
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

    # 9. Save to database
    uploader_id = None  # Can be obtained from token, temporarily set to None
    success, error = database.save_pdf_document(
        title, keywords, keywords_encoded_json, filename, document_date, uploader_id, file_size
    )
    
    if not success:
        return jsonify({
            'success': False,
            'message': f'Failed to save document metadata: {error}'
        }), 500

    # 10. Update keyword database and re-encode all documents
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    success, msg = database.add_keywords_to_db(keyword_list)
    if not success:
        print(f"Warning: Failed to add keywords to database: {msg}")
    
    # Re-encode all documents
    success, msg = database.update_all_documents_encoding()
    if not success:
        print(f"Warning: Failed to update document encodings: {msg}")

    # 11. Return result
    return jsonify({
        'success': True,
        'message': 'Upload succeeded, new RAG files have been generated',
        'pdf': filename,
        'title': title,
        'index_path': index_file,
        'docs_path': docs_file,
        'entries': len(docs)
    }), 200



# Get all PDF files
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
            # Note: Based on current .sql structure, this needs to be modified to match document_date format
            # document_date': doc['document_date'].isoformat() if doc['document_date'] else None,
            'document_date': doc['document_date'] if doc['document_date'] else None,
            'size': doc['file_size'],
            'upload_time': doc['upload_time'].isoformat() if doc['upload_time'] else None
        })
    return jsonify({'success': True, 'pdfs': pdfs})


# Delete specified PDF file
@app.route('/api/admin/deletepdf/<int:document_id>', methods=['DELETE'])
def delete_pdf(document_id):
    # 1. Get document information from database
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
    
    # 2. Delete physical PDF file
    pdf_dir = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(pdf_dir, target_doc['pdf_path'])
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to delete PDF file: {str(e)}'}), 500
    
    # 3. Delete related RAG files
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
    
    # 4. Delete database record
    success, error = database.delete_pdf_document(document_id)
    if not success:
        return jsonify({'success': False, 'error': f'Failed to delete database record: {error}'}), 500
    
    # 5. Update keyword database and re-encode all documents
    # Rebuild keyword database (extract from remaining documents)
    success, msg = database.rebuild_keywords_database()
    if not success:
        print(f"Warning: Failed to rebuild keywords database: {msg}")
    
    # Re-encode all documents
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
    
    # Save user message to database
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

    # 4. Parse LLM response
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = {}
    need_human = False
    
    if data_json is not None:
        final_answer = data_json.get("answer", "")
        final_reference = data_json.get("reference", {})
    else:
        # Fallback: If model doesn't return in JSON format, use content directly as answer
        final_answer = content
        # If parsing fails, human intervention may be needed
        need_human = True

    ai_reply = final_answer
    reference_str = json.dumps(final_reference) if final_reference else None

    # Save AI reply to database, including reference materials and mode information
    database.add_message_db(session_id, 'ai', ai_reply, 
                           reference=reference_str, 
                           mode='general',
                           need_human=need_human)
    
    return jsonify({"answer": ai_reply})


# AI chat RAG mode
@app.route('/api/aichat/rag', methods=['POST'])
def aichat_rag():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    
    # Save user message to database
    database.add_message_db(session_id, 'user', question, mode='rag')

    result = rag_search(question)

    # If rag_search returns {}, it means no relevant results
    if not result:
        # When no relevant materials found, mark as needing human intervention
        database.add_message_db(session_id, 'ai', 
                               "ops, I couldn't find anything, Need I turn to real human?",
                               mode='rag',
                               need_human=True)
        return jsonify({
            "answer": "ops, I couldn't find anything, Need I turn to real human?",
            "reference": {}
        })

    # 2. RAG retrieval
    knowledge, reference = result

    # 3. Construct and request LLM
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

    # 4. Parse LLM response
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = reference  # Default to using RAG reference
    need_human = False

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # If model returns reference, use model's
            final_reference = model_ref
    else:
        # Fallback: If model doesn't return in JSON format, use content directly as answer
        final_answer = content
        # If parsing fails, human intervention may be needed
        need_human = True
    
    ai_reply = final_answer
    reference_str = json.dumps(final_reference) if final_reference else None
    print(reference)

    # Save AI reply to database, including reference materials
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
    Parse text in the form of:
      "Here's a checklist to access your CSE files from your own computer: step1. … step2. …"
    into:
    {
      "answer": "Here's a checklist to access your CSE files from your own computer",
      "checklist": [
         {"item": "Step 1: …", "done": False},
         {"item": "Step 2: …", "done": False},
         ...
      ]
    }
    """
    # 1. Extract answer (content before first colon)
    prefix, _, rest = text.partition(':')
    answer = prefix.strip()

    # 2. Split by stepX. chunks
    chunks = re.split(r'(?=(?:step\d+)\.)', rest)

    items: List[Dict[str, Any]] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # Match stepX. and the description that follows
        m = re.match(r'step(\d+)\.\s*(.*)', chunk, flags=re.DOTALL)
        if m:
            idx = int(m.group(1))
            desc = m.group(2).strip()
            # Construct "Step {idx}: {desc}"
            item_text = f"Step {idx}: {desc}"
            items.append({"item": item_text, "done": False})

    return {
        "answer": answer,
        "checklist": items
    }
# AI chat checklist mode
@app.route('/api/aichat/checklist', methods=['POST'])
def aichat_checklist():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    
    # Save user message to database
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

    # 4. Parse LLM response
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = reference  # Default to using RAG reference
    need_human = False

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        model_ref = data_json.get("reference", {})
        if model_ref:  # If model returns reference, use model's
            final_reference = model_ref
    else:
        # Fallback: If model doesn't return in JSON format, use content directly as answer
        final_answer = content
        # If parsing fails, human intervention may be needed
        need_human = True

    # 3. Call parsing function
    result = parse_checklist_to_items(final_answer)

    # 4. Unpack to ai_reply and checklist
    ai_reply = result["answer"]
    checklist = result["checklist"]
    
    # Convert checklist to JSON string for storage
    checklist_str = json.dumps(checklist) if checklist else None
    reference_str = json.dumps(final_reference) if final_reference else None
    
    # Save AI reply to database, including checklist
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
    # Get real user login statistics
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
    # Get token from request header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get('username')
        
        # Get user detailed information from database
        user = database.get_user(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category', 'subject', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Build feedback data, including user information
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
        
        # Get all admin emails
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
        
        # Send email to all admins
        admin_emails = [admin['email'] for admin in admins]
        
        # Build email content
        subject = f"[HDingo Feedback] {feedback_data['subject']}"
        
        # Email body
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
            # Send email
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

# ==================== New Message Management API ====================

@app.route('/api/admin/messages/need-human', methods=['GET'])
def get_messages_need_human_api():
    """Get all messages that need human intervention"""
    # Admin permission verification can be added here
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
    """Get message statistics information"""
    stats, error = database.get_message_stats_by_mode()
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@app.route('/api/admin/messages/by-mode/<mode>', methods=['GET'])
def get_messages_by_mode_api(mode):
    """Get messages by mode"""
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
    """Mark message as needing human intervention"""
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
    """Update message reference materials"""
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
    """Update message checklist"""
    data = request.get_json() or {}
    checklist = data.get('checklist', [])
    
    # Convert checklist to JSON string
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
    """Get detailed information of a single message"""
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
        
        # Handle boolean conversion and JSON parsing
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
                pass  # Keep original string
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# ==================== Human Support Ticket System API ====================

@app.route('/api/save_ticket', methods=['POST'])
def save_ticket_api():
    """Save human support request ticket"""
    # Get token from request header for authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        staff_id = payload.get('username') or payload.get('id')
        
        if not staff_id:
            return jsonify({
                "success": False,
                "message": "Invalid token: missing user ID"
            }), 401
        
        # Get detailed user information from database
        user = database.get_user(staff_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
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
        
        # Save ticket to database
        ticket_id, error = database.save_ticket(session_id, staff_id, staff_email, content)
        
        if error:
            return jsonify({
                "success": False,
                "message": f"Failed to save ticket: {error}"
            }), 500
        
        # No longer send email, return success directly
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
    """Get ticket list"""
    # Get token from request header for admin permission verification
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_role = payload.get('role')
        
        # Check if user is admin
        if user_role != 'admin':
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        # Get query parameters
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
    """Complete ticket processing"""
    # Get token from request header for admin permission verification
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_role = payload.get('role')
        
        # Check if user is admin
        if user_role != 'admin':
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('ticket_id'):
            return jsonify({
                "success": False,
                "message": "Missing required field: ticket_id"
            }), 400
        
        ticket_id = data.get('ticket_id')
        admin_notes = data.get('admin_notes', '')
        
        # Update ticket status
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
    """Get ticket statistics information"""
    # Get token from request header for admin permission verification
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_role = payload.get('role')
        
        # Check if user is admin
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
    """Get single ticket details"""
    # Get token from request header for permission verification
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_role = payload.get('role')
        user_id = payload.get('username') or payload.get('id')
        
        # Get ticket details
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
        
        # Permission check: Admin can view all tickets, regular users can only view their own tickets
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
    """Get current user's ticket list"""
    # Get token from request header for authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "Authorization token required"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        staff_id = payload.get('username') or payload.get('id')
        
        if not staff_id:
            return jsonify({
                "success": False,
                "message": "Invalid token: missing user ID"
            }), 401
        
        # Get query parameters
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

# New/old layout switching and saving
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


# Mock AI chat API for frontend development

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
    # Save user message to database
    database.add_message_db(session_id, 'user', question, mode='general')

    # AI generation part modification here vvv
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
                    "  - \"answer\": string (the final answer) in markdown\n"
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

    # 4. Parse LLM response
    content = result['choices'][0]['message']['content'].strip()
    data_json, err = try_load_json(content)

    final_answer = ""
    final_reference = {}
    need= False

    if data_json is not None:
        final_answer = data_json.get("answer", "")
        final_reference = data_json.get("reference", {})
    else:
        # Fallback: If model doesn't return in JSON format, use content directly as answer
        final_answer = content
        # If parsing fails, human intervention may be needed
        need= True

    if need:
        # Need human intervention
        ai_reply = "AI cant answer this question.  \n\nYou can press the button below to ask for human help."
        # Save reply to database
        database.add_message_db(session_id, 'ai', ai_reply, mode='general', need_human=True)
        return jsonify({
            "answer": ai_reply,
            "reference": [],
            "checklist": [],
            "mode": "general",
            "need_human": True
        })
    else:
        # No human intervention needed
        ai_reply = final_answer
        # Save reply to database
        database.add_message_db(session_id, 'ai', ai_reply, mode='general')
        # Return to frontend
        return jsonify({
            "answer": ai_reply,
            "reference": [],
            "checklist": [],
            "mode": "general",
            "need_human": False
        })

    # AI generation part modification here ^^^




@app.route('/api/aichat/mock/rag', methods=['POST'])
def aichat_rag_mock():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question, mode='rag')

# RAG search
    result = rag_search(question)
    need = False
    # If rag_search returns {}, it means no relevant results
    if not result:
        need = True
        # # When no relevant materials found, mark as needing human intervention
        # database.add_message_db(session_id, 'ai',
        #                         "ops, I couldn't find anything, Need I turn to real human?",
        #                         mode='rag',
        #                         need_human=True)
    else:
        # 2. RAG retrieval
        knowledge, reference = result

        # 3. Construct and request LLM
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

        # 4. Parse LLM response
        content = result['choices'][0]['message']['content'].strip()
        data_json, err = try_load_json(content)

        final_reference = reference  # Default to using RAG reference
        print(final_reference)

        if data_json is not None:
            final_answer = data_json.get("answer", "")
            # model_ref = data_json.get("reference", {})
            # if model_ref:  # If model returns reference, use model's
            #     final_reference = model_ref
        else:
            # Fallback: If model doesn't return in JSON format, use content directly as answer
            final_answer = content
            # If parsing fails, human intervention may be needed
            need = True

    if need:
        # Need human intervention
        ai_reply = "There is no reference for this RAG question.  \n\nYou can press the button below to ask for human help."

        database.add_message_db(session_id, 'ai', ai_reply, need_human=need, mode='rag')
        return jsonify({
            "answer": ai_reply,
            "reference": [],
            "checklist": [],
            "mode": "rag",
            "need_human": True
        })
    else:
        # No human intervention needed, reference needs to be saved to database
        ai_reply = final_answer
        ai_reference = final_reference
        # ai_reply = "I can find the answer in the following documents."
        # ai_reference = {
        #     # If there's an issue with PDF not opening in frontend, check if dictionary value follows this format, especially underscores
        #     "Account_Disabled_-_CSE_taggi": "http://localhost:8000/pdfs/Account_Disabled_-_CSE_taggi.pdf",
        #     # "Account_expiry_-_CSE_taggi": "http://localhost:8000/pdfs/Account_expiry_-_CSE_taggi.pdf"
        # }
        # Save AI reply to database, reference also needs to be saved to database
        # Need to convert dictionary to JSON string
        reference_str = json.dumps(ai_reference) if ai_reference else None
        database.add_message_db(session_id, 'ai', ai_reply, reference=reference_str, need_human=need, mode='rag')
        return jsonify({
            "answer": ai_reply,
            "reference": ai_reference,
            "checklist": [],
            "mode": "rag",
            "need_human": False
        })
import re
from typing import Any, Dict, List

import re
from typing import Any, Dict, List

def checklist_to_items(text: str) -> Dict[str, Any]:
    """
    Parse text in the form of:
      "Here's a checklist ...: step1. … step2. …"
    or
      "Here's a checklist ...:\n1. …\n2. …\n..."
    into:
    {
      "answer": "...",
      "ai_checklist": [
         "Step 1: …",
         "Step 2: …",
         ...
      ]
    }
    Also removes Markdown formatting symbols from input.
    """
    # 1. Extract answer (content before first colon)
    prefix, sep, rest = text.partition(':')
    answer = prefix.strip()
    body = rest if sep else text  # If no colon, use entire text as body

    # 2. First try using stepX. chunks
    step_chunks = re.split(r'(?=(?:step\d+)\.)', body, flags=re.IGNORECASE)
    items: List[str] = []

    for chunk in step_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r'step(\d+)\.\s*(.*)', chunk, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            continue
        idx = int(m.group(1))
        desc = m.group(2).strip()
        desc = re.sub(r'[`*_~]', '', desc)
        items.append(f"Step {idx}: {desc}")

    # 3. If no stepX., parse by numbered list (1. 2. 3.)
    if not items:
        lines = body.splitlines()
        idx_counter = 0
        for line in lines:
            line = line.strip()
            m = re.match(r'(\d+)\.\s*(.*)', line)
            if not m:
                continue
            idx_counter += 1
            desc = m.group(2).strip()
            desc = re.sub(r'[`*_~]', '', desc)
            items.append(f"Step {idx_counter}: {desc}")

    return {
        "answer": answer,
        "ai_checklist": items
    }


@app.route('/api/aichat/mock/checklist', methods=['POST'])
def aichat_checklist_mock():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    if not question or not session_id:
        return jsonify({"error": "question and session_id cannot be empty"}), 400
    database.add_message_db(session_id, 'user', question)

    result = rag_search(question)

    need = False
    # If rag_search returns {}, it means no relevant results
    if not result:
        need = True
        # # When no relevant materials found, mark as needing human intervention
        # database.add_message_db(session_id, 'ai',
        #                         "ops, I couldn't find anything, Need I turn to real human?",
        #                         mode='rag',
        #                         need_human=True)
    else:
        # 2. RAG retrieval
        knowledge, reference = result

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

        # 4. Parse LLM response
        content = result['choices'][0]['message']['content'].strip()
        data_json, err = try_load_json(content)

        final_reference = reference  # Default to using RAG reference

        if data_json is not None:
            final_answer = data_json.get("answer", "")
            # model_ref = data_json.get("reference", {})
            # if model_ref:  # If model returns reference, use model's
            #     final_reference = model_ref
        else:
            # Fallback: If model doesn't return in JSON format, use content directly as answer
            final_answer = content
            # If parsing fails, human intervention may be needed
            need= True
        # print(final_answer)
        # 3. Call parsing function
        result = checklist_to_items(final_answer)
        # print(result)
        # 4. Unpack to ai_reply and checklist
        ai_reply = result["answer"]
        ai_checklist = result["ai_checklist"]
        """-----Output result always returns 500---"""
        """--------Here is AI result reference--------"""
        # print("AI reply:", ai_reply)
        # for item in ai_checklist:
        #     print("-", item)
        # ai_reference=final_reference
        # print(ai_reference)
        """--------Here is AI result reference--------"""
    if need:
        # Need human intervention
        ai_reply = "There is no reference for this Checklist question.  \n\nYou can press the button below to ask for human help."

        database.add_message_db(session_id, 'ai', ai_reply, need_human=need, mode='checklist')
        return jsonify({
            "answer": ai_reply,
            "reference": [],
            "checklist": [],
            "mode": "checklist",
            "need_human": True
        })
    else:
        # # No human intervention needed, checklist needs to be saved to database
        # ai_reply = "Here's a checklist to access your CSE files from your own computer:"
        # ai_reference = {
        #     # If there's an issue with PDF not opening in frontend, check if dictionary value follows this format, especially underscores
        #     "Account_expiry_-_CSE_taggi": "http://localhost:8000/pdfs/Account_expiry_-_CSE_taggi.pdf"
        # }
        #
        # # AI generation part, let AI generated checklist be stored in this variable (may need string splitting and other processing before putting here)
        # ai_checklist = [
        #     "Step 1: Login to CSE file server (sftp.cse.unsw.edu.au)",
        #     "Step 2: Use your CSE username and password for authentication",
        #     "Step 3: Navigate to your home directory (/home/your_username)",
        #     "Step 4: Create or select directory to upload files",
        #     "Step 5: Use put command to upload files to server",
        #     "Step 6: Verify file upload success and check file permissions"
        # ]
        #
        # Directly convert to checklist items format, conforming to database format
        ai_checklist_items = [
            {
                "item": item,
                "done": False
            }
            for item in ai_checklist
        ]

        # Save AI reply to database, including checklist and reference
        # reference_str = json.dumps(ai_reference) if ai_reference else None
        reference_str = json.dumps(final_reference) if final_reference else None
        checklist_str = json.dumps(ai_checklist_items) if ai_checklist_items else None
        success, message_id, error = database.add_message_db(session_id, 'ai', ai_reply, 
                                                            reference=reference_str, 
                                                            checklist=checklist_str,
                                                            mode='checklist',
                                                            need_human=False)
        
        if not success:
            return jsonify({"error": f"Failed to save message: {error}"}), 500
        
        # When checklist returns successfully, also need to return a message_id for frontend to update checklist status
        return jsonify({
            "answer": ai_reply,
            # "reference": ai_reference,
            "reference": final_reference,
            "checklist": ai_checklist_items,
            "mode": "checklist",
            "need_human": False,
            "message_id": message_id
        })

@app.route('/api/message/<int:message_id>/update-checklist-item', methods=['POST'])
def update_checklist_item_api(message_id):
    """
    Update the status of a single checklist item
    """
    data = request.get_json() or {}
    item_index = data.get('item_index')
    checked = data.get('checked', False)
    
    if item_index is None:
        return jsonify({'success': False, 'error': 'item_index is required'}), 400
    
    try:
        item_index = int(item_index)
    except ValueError:
        return jsonify({'success': False, 'error': 'item_index must be an integer'}), 400
    
    success, error = database.update_checklist_item_status(message_id, item_index, checked)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Checklist item status updated successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 400

@app.route('/api/reply_ticket', methods=['POST'])
def reply_ticket_api():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    admin_notes = data.get('admin_notes')
    if not ticket_id or not admin_notes:
        return jsonify({"success": False, "message": "Missing ticket_id or admin_notes"}), 400

    # Get admin information
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Authorization token required"}), 401
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        admin_id = payload.get('username') or payload.get('id')
        admin_user = database.get_user(admin_id)
        admin_name = f"{admin_user.get('first_name', '')} {admin_user.get('last_name', '')}" if admin_user else admin_id
    except Exception as e:
        admin_name = "(unknown admin)"

    # 1. Find ticket
    ticket, error = database.get_ticket_by_id(ticket_id)
    if error or not ticket:
        return jsonify({"success": False, "message": "Ticket not found"}), 404

    # 2. Send email to user
    subject = f"[HDingo Support] Your ticket #{ticket_id} has been answered"
    body = f"""
Dear {ticket['first_name']} {ticket['last_name']}:

Your human support request has been answered by our admin team. Please see the reply below:

---
{admin_notes}
---

Replied by: {admin_name}

If you have further questions, feel free to reply or submit a new ticket.

This email was sent automatically by HDingo system.
Ticket content:
{ticket['content']}

Request time: {ticket['request_time']}
""".strip()
    try:
        msg = Message(
            subject=subject,
            recipients=[ticket['staff_email']],
            body=body
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending reply email to user: {str(e)}")
        return jsonify({"success": False, "message": "Failed to send email to user"}), 500

    # 3. Update ticket status to processed
    success, error = database.finish_ticket(ticket_id, admin_notes)
    if not success:
        return jsonify({"success": False, "message": "Failed to update ticket status"}), 500

    return jsonify({"success": True, "message": "Reply sent and ticket updated"})

if __name__ == '__main__':
    app.run(debug=True, port=8000)
