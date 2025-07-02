from flask import Flask, request, jsonify
from flask_cors import CORS
from search import extract_keywords, multi_hot_encode, calculate_similarity, DATABASE
import requests 

app = Flask(__name__)
CORS(app)

# ———— AI 聊天配置区域 ————
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL   = "Qwen/QwQ-32B"
API_KEY = "sk-xlrowobsoqpeykasamsgwlbjiilruinjklvbryuvbiukhekt"
# ————————————————————

# ---- 测试接口 ----
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")

# ---- 假用户数据 ----
# 暂定 staff 身份可区分为 phd, tutor, lecturer, none
# 用布尔 admin 来区分是否为管理员
fake_users = [
    {"username": "phd1", "password": "pass123", "email": "staff1@example.com", "role": "phd", "admin": False},
    {"username": "tutor1", "password": "pass123", "email": "staff1@example.com", "role": "tutor", "admin": False},
    {"username": "lecturer1", "password": "pass123", "email": "staff1@example.com", "role": "lecturer", "admin": False},
    {"username": "admin1", "password": "adminpass", "email": "admin1@example.com","role": "none", "admin": True},
    # 可以继续添加更多账号
]

# ---- 登录接口, 在 staff login 页面调用 ----
@app.route('/api/staff-login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 模拟查找用户
    user = next((u for u in fake_users if u["username"] == username), None)
    if user and user["password"] == password:
        return jsonify({"success": True, "role": user["role"], "message": "Login success!"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

# ---- SSO登录模拟 ----
@app.route('/api/sso-login', methods=['GET'])
def sso_login():
    # 实际项目会重定向到UNSW SSO登录页，这里仅做演示，直接“登录成功”
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
            "url": item["url"],
            "score": score
        })

    # 按分数排序，只返回相关度>0的前5个
    filtered = sorted([r for r in results if r["score"] > 0], key=lambda x: x["score"], reverse=True)[:5]

    return jsonify({"results": filtered})

# profile接口暂时不使用，因为前端没有调用
'''
@app.route('/api/profile', methods=['GET'])
def profile():
    # 从 URL 查询参数获取用户名，如 /api/profile?username=staff1
    username = request.args.get("username")
    if username:
        # 查找匹配的用户
        user = next((u for u in fake_users if u["username"] == username), None)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
    else:
        # 未指定用户名，默认返回第一个用户（适合 demo 环境）
        user = fake_users[0]
    return jsonify({
        "success": True,
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    })
'''

# logout暂时不使用，因为前端没有掉用
'''
@app.route('/api/logout', methods=['POST'])
def logout():
    """
    前端调用此接口时，后端返回登出成功消息。
    如果将来引入 session 或 token，可以在此处清理 session/token。
    """
    # TODO: 若有 session，使用 session.clear() 等方法进行清理
    # session.clear()

    # TODO: 若有 token，返回前端指示删除本地 token
    return jsonify({"success": True, "message": "Logout success!"})
'''

# ---- 首页（仅演示跳转用）----
@app.route('/')
def home():
    return 'Welcome to the demo backend!'

# ---- AI 聊天接口 ----
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "question 不能为空"}), 400

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": question}
        ]
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

if __name__ == '__main__':
    app.run(debug=True, port=8000)
