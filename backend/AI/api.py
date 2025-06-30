from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# ———— 配置区域 ————
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL   = "Qwen/QwQ-32B"
API_KEY = "sk-xlrowobsoqpeykasamsgwlbjiilruinjklvbryuvbiukhekt"
# ——————————————————

# 创建 Flask 应用，把 static_folder 指向 static/
app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/ask', methods=['POST'])
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

@app.route('/')
def index():
    # 直接返回 static/index.html
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
