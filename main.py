from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, supports_credentials=True)

# API Keys
AVIATION_API_KEY = "7637add89f019adafaf3d96030a66f6d"
SKYSCANNER_API_KEY = "01fb0a41d2msh011b5606760bb91p1617b0jsn910dff2ba870"

# Danh sách sân bay hợp lệ
VALID_AIRPORTS = {"HAN": "Nội Bài", "SGN": "Tân Sơn Nhất", "DAD": "Đà Nẵng"}
VALID_TIMES = ["SÁNG", "CHIỀU", "TỐI"]

# Bộ nhớ tạm cho người dùng
user_sessions = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.json.get("user_id")
    user_message = request.json.get("message", "").strip().upper()

    if not user_id or not user_message:
        return jsonify({"bot": "Xin hãy nhập thông tin hợp lệ!"})

    # Kiểm tra nếu user chưa có session
    if user_id not in user_sessions:
        user_sessions[user_id] = {"step": 1}

    session = user_sessions[user_id]

    # === Xử lý các bước chatbot ===
    if session["step"] == 1:
        if user_message not in VALID_AIRPORTS:
            return jsonify({"bot": "Vui lòng nhập mã sân bay hợp lệ (HAN, SGN, DAD)."})
        session["departure"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn bay đến đâu? (HAN, SGN, DAD)"})

    elif session["step"] == 2:
        if user_message not in VALID_AIRPORTS or user_message == session["departure"]:
            return jsonify({"bot": "Vui lòng nhập điểm đến khác điểm đi (HAN, SGN, DAD)."})
        session["arrival"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn bay vào buổi nào? (Sáng, Chiều, Tối)"})

    elif session["step"] == 3:
        if user_message not in VALID_TIMES:
            return jsonify({"bot": "Vui lòng nhập 'Sáng', 'Chiều' hoặc 'Tối'."})
        session["time"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn xem tất cả chuyến bay hay chỉ chuyến rẻ nhất? (Tất cả / Chuyến bay rẻ nhất)"})

    elif session["step"] == 4:
        session["option"] = user_message.lower()
        session["step"] += 1
        return jsonify({"bot": f"Đang tìm chuyến bay từ {session['departure']} đến {session['arrival']} vào buổi {session['time']}..."})

    return jsonify({"bot": "Xin lỗi, tôi không hiểu câu hỏi của bạn!"})

if __name__ == "__main__":
    app.run(debug=True)
