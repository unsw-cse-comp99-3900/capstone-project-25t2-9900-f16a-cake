from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---- 测试接口 ----
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")

# ---- 假用户数据 ----
fake_users = [
    {"username": "staff1", "password": "pass123", "role": "staff"},
    {"username": "admin1", "password": "adminpass", "role": "admin"},
    # 可以继续添加更多账号
]

# ---- 登录接口 ----
@app.route('/api/login', methods=['POST'])
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

# ---- 首页（仅演示跳转用）----
@app.route('/')
def home():
    return 'Welcome to the demo backend!'

if __name__ == '__main__':
    app.run(debug=True, port=8000)
