from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask! This is my test message, yeah!")

if __name__ == "__main__":
    app.run(debug=True)
