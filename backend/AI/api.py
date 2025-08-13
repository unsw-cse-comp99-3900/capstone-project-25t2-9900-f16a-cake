"""
Flask-based Chat API Gateway for SiliconFlow Qwen/QwQ-32B Model

This project provides a simple HTTP API endpoint (`/ask`) to handle chat requests
from a frontend and forward them to the SiliconFlow API. It wraps the interaction
with the Qwen/QwQ-32B large language model, handles CORS for browser-based clients,
and serves a static HTML frontend from the `static/` directory.

Main Features:
- Accepts POST requests with a 'question' payload.
- Sends the question to SiliconFlow's `chat/completions` endpoint.
- Returns the AI-generated answer to the client in JSON format.
- Serves the frontend from the `/` route.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# ———— Configuration Section ————
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL   = "Qwen/QwQ-32B"
API_KEY = "sk-xlrowobsoqpeykasamsgwlbjiilruinjklvbryuvbiukhekt"
# ——————————————————

# Create the Flask application and set the static folder to `static/`
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

    # call SiliconFlow API
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    result = resp.json()

    # Extract the model's answer
    answer = result['choices'][0]['message']['content'].strip()
    return jsonify({"answer": answer})

@app.route('/')
def index():
    # return static/index.html
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
