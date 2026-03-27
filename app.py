from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)
# Load API key from environment variable for production deployment
api_key = "40a16ed70c201e66f700607b856f39c7"
# simple in-memory search history (could be persisted to file)
search_history = []
MAX_HISTORY = 10

@app.route('/')
def index():
    # This loads the blank starting page. We set a default 'day' vibe.
    return render_template('index.html', time_vibe='day')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city') # Use .form.get if using a standard HTML form
    
    # --- YOUR API CALL CODE STARTS HERE ---
    # (Keep the lines where you fetch 'data' from OpenWeather)
    # --- YOUR API CALL CODE ENDS HERE ---

    # 1. Extract the specific data points from the JSON
    weather_info = data['weather'][0]['main']
    sunrise = data['sys']['sunrise']
    sunset = data['sys']['sunset']
    current_time = data['dt']

    # 2. Logic to decide if it's Day or Night
    if sunrise <= current_time <= sunset:
        vibe = "day"
    else:
        vibe = "night"

    # 3. Send EVERYTHING to the HTML in one go
    return render_template('index.html', 
                           condition=weather_info, 
                           time_vibe=vibe, 
                           data=data)


   
weather_info = data['weather'][0]['main'] 

# Now update your return line to this:
return render_template('index.html', condition=weather_info)

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.json.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400
    
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            # basic info
            weather_info = {
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'icon': data['weather'][0]['icon'],
                'lat': data['coord']['lat'],
                'lon': data['coord']['lon'],
                'sunrise': data['sys']['sunrise'],
                'sunset': data['sys']['sunset'],
                'precipitation': data.get('rain', {}).get('1h', 0)
            }
            # uv index via onecall
            try:
                one_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={weather_info["lat"]}&lon={weather_info["lon"]}&exclude=minutely,hourly,daily,alerts&appid={api_key}'
                one_resp = requests.get(one_url)
                one_data = one_resp.json()
                weather_info['uvi'] = one_data.get('current', {}).get('uvi')
            except:
                weather_info['uvi'] = None

            # update history
            fullcity = f"{data['name']}, {data['sys']['country']}"
            if fullcity not in search_history:
                search_history.insert(0, fullcity)
                if len(search_history) > MAX_HISTORY:
                    search_history.pop()
            return jsonify(weather_info)
        else:
            return jsonify({'error': data.get('message', 'City not found')}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forecast', methods=['POST'])
def get_forecast():
    city = request.json.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400
    
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            forecasts = []
            for item in data['list'][::8]:  # Every 24 hours
                forecasts.append({
                    'date': datetime.fromtimestamp(item['dt']).strftime('%a, %b %d'),
                    'temp': round(item['main']['temp']),
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon']
                })
            return jsonify({'forecasts': forecasts[:5]})
        else:
            return jsonify({'error': 'Forecast not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hourly', methods=['POST'])
def get_hourly():
    city = request.json.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
    try:
        resp = requests.get(url)
        data = resp.json()
        if resp.status_code == 200:
            hours = []
            for item in data['list'][:24]:
                hours.append({
                    'time': datetime.fromtimestamp(item['dt']).strftime('%H:%M'),
                    'temp': round(item['main']['temp']),
                    'icon': item['weather'][0]['icon']
                })
            return jsonify({'hours': hours})
        else:
            return jsonify({'error': 'Hourly data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    return jsonify({'history': search_history})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
import os
from dotenv import load_dotenv

load_dotenv()
if __name__ == "__main__":
    # This tells the app to use the Port Render gives it, or 5000 as a backup
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
