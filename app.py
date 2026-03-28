import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('OPENWEATHER_API_KEY', '40a16ed70c201e66f700607b856f39c7')
search_history = []
favorites = []
MAX_HISTORY = 10

def fetch_weather(city):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    resp = requests.get(url)
    if resp.status_code != 200:
        return None, resp

    data = resp.json()

    info = {
        'city': data.get('name'),
        'country': data.get('sys', {}).get('country'),
        'temperature': round(data.get('main', {}).get('temp', 0)),
        'feels_like': round(data.get('main', {}).get('feels_like', 0)),
        'description': data.get('weather', [{}])[0].get('description', ''),
        'humidity': data.get('main', {}).get('humidity'),
        'pressure': data.get('main', {}).get('pressure'),
        'wind_speed': data.get('wind', {}).get('speed'),
        'icon': data.get('weather', [{}])[0].get('icon'),
        'lat': data.get('coord', {}).get('lat'),
        'lon': data.get('coord', {}).get('lon'),
        'sunrise': data.get('sys', {}).get('sunrise'),
        'sunset': data.get('sys', {}).get('sunset'),
        'precipitation': data.get('rain', {}).get('1h', 0) if isinstance(data.get('rain', {}), dict) else 0,
    }

    if info['lat'] is not None and info['lon'] is not None:
        one_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={info["lat"]}&lon={info["lon"]}&exclude=minutely,hourly,daily,alerts&appid={API_KEY}&units=metric'
        one_resp = requests.get(one_url)
        if one_resp.status_code == 200:
            one_data = one_resp.json()
            info['uvi'] = one_data.get('current', {}).get('uvi')
        else:
            info['uvi'] = None
    else:
        info['uvi'] = None

    return info, resp


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather', methods=['POST'])
def get_weather():
    payload = request.get_json(force=True, silent=True) or {}
    city = payload.get('city') or request.form.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    info, resp = fetch_weather(city)
    if resp.status_code != 200 or info is None:
        message = resp.json().get('message', 'City not found') if resp is not None else 'Error fetching weather'
        return jsonify({'error': message}), 404

    fullcity = f"{info['city']}, {info['country']}"
    if fullcity not in search_history:
        search_history.insert(0, fullcity)
        if len(search_history) > MAX_HISTORY:
            search_history.pop()

    sunrise = info.get('sunrise')
    sunset = info.get('sunset')
    current = int(datetime.utcnow().timestamp())
    info['time_vibe'] = 'day' if sunrise and sunset and sunrise <= current <= sunset else 'night'

    return jsonify(info)


@app.route('/forecast', methods=['POST'])
def get_forecast():
    payload = request.get_json(force=True, silent=True) or {}
    city = payload.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric'
    resp = requests.get(url)
    if resp.status_code != 200:
        return jsonify({'error': 'Forecast not found'}), 404

    data = resp.json()
    forecasts = []
    for item in data.get('list', [])[::8]:
        dt = item.get('dt')
        forecasts.append({
            'date': datetime.fromtimestamp(dt).strftime('%a, %b %d') if dt else '',
            'temp': round(item.get('main', {}).get('temp', 0)),
            'description': item.get('weather', [{}])[0].get('description', ''),
            'icon': item.get('weather', [{}])[0].get('icon', '')
        })

    return jsonify({'forecasts': forecasts[:5]})


@app.route('/hourly', methods=['POST'])
def get_hourly():
    payload = request.get_json(force=True, silent=True) or {}
    city = payload.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric'
    resp = requests.get(url)
    if resp.status_code != 200:
        return jsonify({'error': 'Hourly data not found'}), 404

    data = resp.json()
    hours = []
    for item in data.get('list', [])[:24]:
        dt = item.get('dt')
        hours.append({
            'time': datetime.fromtimestamp(dt).strftime('%H:%M') if dt else '',
            'temp': round(item.get('main', {}).get('temp', 0)),
            'icon': item.get('weather', [{}])[0].get('icon', '')
        })

    return jsonify({'hours': hours})


@app.route('/history', methods=['GET'])
def history():
    return jsonify({'history': search_history})


@app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
def handle_favorites():
    global favorites
    if request.method == 'GET':
        return jsonify(favorites)

    payload = request.get_json(force=True, silent=True) or {}
    city = payload.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    if request.method == 'POST':
        if city not in favorites:
            favorites.append(city)
        return jsonify({'favorites': favorites})

    if request.method == 'DELETE':
        if city in favorites:
            favorites.remove(city)
        return jsonify({'favorites': favorites})


@app.route('/reverse', methods=['GET'])
def reverse_geocode():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    url = f'https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}'
    resp = requests.get(url)
    if resp.status_code != 200:
        return jsonify({'error': 'Reverse geocode failed'}), 500

    data = resp.json()
    if not data:
        return jsonify({'error': 'Location not found'}), 404

    first = data[0]
    return jsonify({'city': first.get('name')})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
