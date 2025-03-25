from fastapi import FastAPI, Query
import requests
import uvicorn
import webbrowser
import threading
from fastapi.staticfiles import StaticFiles

app = FastAPI()

AMADEUS_API_KEY = "r9OvcpKZGVUkqvcqxf1QP3bHjZdx87nT"
AMADEUS_API_SECRET = "9ISfyagdCA1F09gr"

def open_browser():
    """Mở giao diện UI trên trình duyệt mặc định sau khi server khởi động"""
    webbrowser.open("http://127.0.0.1:8000")

def get_amadeus_access_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

@app.get("/search_flight")
def search_flight(
    from_city: str = Query(..., description="Điểm khởi hành"),
    to_city: str = Query(..., description="Điểm đến"),
    date: str = Query(..., description="Ngày bay (YYYY-MM-DD)")
):
    token = get_amadeus_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    params = {
        "originLocationCode": from_city,
        "destinationLocationCode": to_city,
        "departureDate": date,
        "adults": 1,
        "currencyCode": "VND"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    flights = []
    for flight in data.get("data", []):
        itinerary = flight["itineraries"][0]
        segment = itinerary["segments"][0]
        flight_info = {
            "id": flight["id"],
            "carrier": segment["carrierCode"],
            "flight_number": segment["number"],
            "departure": segment["departure"]["iataCode"],
            "departure_time": segment["departure"]["at"],
            "arrival": segment["arrival"]["iataCode"],
            "arrival_time": segment["arrival"]["at"],
            "duration": itinerary["duration"],
            "stops": segment["numberOfStops"],
            "price": float(flight["price"]["grandTotal"])  # Chuyển thành float để dễ sắp xếp
        }
        flights.append(flight_info)

    # **Sắp xếp danh sách theo giá vé từ thấp đến cao**
    flights.sort(key=lambda x: x["price"])

    # **Chỉ lấy tối đa 5 chuyến bay rẻ nhất**
    top_flights = flights[:5] if flights else []

    return {"flights": top_flights if top_flights else "Không tìm thấy chuyến bay phù hợp"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
