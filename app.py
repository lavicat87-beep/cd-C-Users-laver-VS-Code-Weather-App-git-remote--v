from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)


API_KEY = '40a16ed70c201e66f700607b856f39c7' 

@app.route('/')
def index():
    return render_template('index.html', time_vibe='day')

@app.route('/weather', methods=['POST'])
def get_weather():
    city = request.form.get('city')
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json() 

    if response.status_code == 200:
        # 3. Logic for your "Sun and Moon" theme
        # We check the current time (dt) against sunrise and sunset
        sunrise = data['sys']['sunrise']
        sunset = data['sys']['sunset']
        current_time = data['dt']
        
        vibe = "day" if sunrise <= current_time <= sunset else "night"
        
        # 4. SEND TO HTML
        # This matches the {{ data }}, {{ condition }}, and {{ time_vibe }} in your index.html
        return render_template('index.html', 
                               data=data, 
                               condition=data['weather'][0]['main'], 
                               time_vibe=vibe)
    else:
        # If the city is wrong or API fails
        return render_template('index.html', error="City not found", time_vibe='day')

    
    # 3. Pull the info out of the data
    weather_info = data['weather'][0]['main'] 

    return render_template('index.html', condition=weather_info, data=data)
    
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
