from flask import Flask, request, jsonify
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

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.json.get("user_id")
    user_message = request.json.get("message", "").strip().upper()

    print(f"🛠 Received request from {user_id}: {user_message}")

    if not user_id or not user_message:
        return jsonify({"bot": "Xin hãy nhập thông tin hợp lệ!"})

    # Kiểm tra nếu user chưa có session
    if user_id not in user_sessions:
        user_sessions[user_id] = {"step": 1}
        print(f"🔹 Created new session for {user_id}")

    session = user_sessions[user_id]
    print(f"🛠 Current session state: {session}")

    # === BƯỚC 1: Chọn điểm xuất phát ===
    if session["step"] == 1:
        if user_message not in VALID_AIRPORTS:
            return jsonify({"bot": "Vui lòng nhập mã sân bay hợp lệ (HAN, SGN, DAD)."})

        session["departure"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn bay đến đâu? (HAN, SGN, DAD)"})

    # === BƯỚC 2: Chọn điểm đến ===
    elif session["step"] == 2:
        if user_message not in VALID_AIRPORTS:
            return jsonify({"bot": "Vui lòng nhập mã sân bay hợp lệ (HAN, SGN, DAD)."})
        
        if user_message == session["departure"]:
            return jsonify({"bot": "Điểm đến không thể trùng với điểm đi! Vui lòng nhập lại."})

        session["arrival"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn bay vào buổi nào? (Sáng, Chiều, Tối)"})

    # === BƯỚC 3: Chọn thời gian bay ===
    elif session["step"] == 3:
        if user_message not in VALID_TIMES:
            return jsonify({"bot": "Vui lòng nhập 'Sáng', 'Chiều' hoặc 'Tối'."})

        session["time"] = user_message
        session["step"] += 1
        return jsonify({"bot": "Bạn muốn xem tất cả chuyến bay hay chỉ chuyến rẻ nhất? (Tất cả / Chuyến bay rẻ nhất)"})

    # === BƯỚC 4: Chọn loại chuyến bay ===
    elif session["step"] == 4:
        user_message = user_message.lower()
        if user_message not in ["tất cả", "chuyến bay rẻ nhất"]:
            return jsonify({"bot": "Vui lòng nhập 'Tất cả' hoặc 'Chuyến bay rẻ nhất'."})

        session["option"] = user_message
        session["step"] +=1

        print(f"🔹 Fetching flights from {session['departure']} to {session['arrival']}")

        # === Gọi API để lấy thông tin chuyến bay ===
        aviation_url = f"http://api.aviationstack.com/v1/flights?access_key={AVIATION_API_KEY}&dep_iata={session['departure']}&arr_iata={session['arrival']}"
        try:
            aviation_response = requests.get(aviation_url).json()
            print(f"✅ Aviation API response: {aviation_response}")
        except Exception as e:
            print(f"❌ Error calling Aviation API: {e}")
            return jsonify({"bot": "Lỗi khi lấy dữ liệu chuyến bay. Vui lòng thử lại sau."})

        if "data" not in aviation_response or not aviation_response["data"]:
            return jsonify({"bot": "Không tìm thấy chuyến bay nào với thông tin này!"})

        flights = aviation_response["data"]

        # === Gọi API lấy giá vé ===
        skyscanner_url = f"https://skyscanner44.p.rapidapi.com/search?from={session['departure']}&to={session['arrival']}&depart=2024-04-10&return=2024-04-15&adults=1&currency=VND"
        headers = {"X-RapidAPI-Key": SKYSCANNER_API_KEY}
        try:
            skyscanner_response = requests.get(skyscanner_url, headers=headers).json()
            print(f"✅ Skyscanner API response: {skyscanner_response}")
        except Exception as e:
            print(f"❌ Error calling Skyscanner API: {e}")
            return jsonify({"bot": "Lỗi khi lấy dữ liệu giá vé. Vui lòng thử lại sau."})

        if "itineraries" not in skyscanner_response:
            return jsonify({"bot": "Hiện tại không thể lấy dữ liệu giá vé, vui lòng thử lại sau."})

        # Xử lý dữ liệu giá vé
        flight_prices = {}
        for itinerary in skyscanner_response.get("itineraries", []):
            legs = itinerary.get("legs", [])
            if legs and "id" in legs[0]:
                price = itinerary.get("pricing_options", [{}])[0].get("price", {}).get("amount", None)
                if price is not None:
                    flight_prices[legs[0]["id"]] = price

        # Sắp xếp chuyến bay theo giá vé
        flights_sorted = sorted(flights, key=lambda x: flight_prices.get(x.get('flight', {}).get('iata', ''), float('inf')))

        if not flights_sorted:
            return jsonify({"bot": "Không có chuyến bay phù hợp với thông tin của bạn."})

        # === Trả về kết quả cho người dùng ===
        if session["option"] == "chuyến bay rẻ nhất":
            cheapest_flight = flights_sorted[0]
            return jsonify({
                "bot": f"✈ Chuyến bay rẻ nhất:\nHãng: {cheapest_flight.get('airline', {}).get('name', 'Không rõ')}\nGiá: {flight_prices.get(cheapest_flight.get('flight', {}).get('iata', ''), 'Không có thông tin')} VND"
            })
        else:
            top_3_flights = flights_sorted[:3]
            return jsonify({
                "bot": "\n\n".join([
                    f"✈ {f.get('flight', {}).get('iata', 'N/A')} - {f.get('airline', {}).get('name', 'Không rõ')} - {flight_prices.get(f.get('flight', {}).get('iata', ''), 'Không có thông tin')} VND"
                    for f in top_3_flights
                ])
            })

    return jsonify({"bot": "Xin lỗi, tôi không hiểu câu hỏi của bạn!"})

if __name__ == "__main__":
    app.run(debug=True)
