#######################
# Pet Planter AI Code #
#######################

from flask import Flask, render_template_string, request, redirect, url_for, session
import requests
import json
from datetime import datetime

# URLs for Adafruit IO feeds
MOISTURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/moisture/data?limit=1"
TEMPERATURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/temperature/data?limit=1"
AMBIENT_LIGHT_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/ambient/data?limit=1"
UV_LIGHT_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/uv/data?limit=1"

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management

# --- Core logic reused from original script ---
def fetch_latest_feed_value(feed_url):
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]["value"], data[0]["created_at"]
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching data from {feed_url}: {e}")
        return None, None

def get_latest_sensor_data():
    moisture, moisture_time = fetch_latest_feed_value(MOISTURE_FEED_URL)
    temperature, temperature_time = fetch_latest_feed_value(TEMPERATURE_FEED_URL)
    ambient_light, ambient_time = fetch_latest_feed_value(AMBIENT_LIGHT_FEED_URL)
    uv_light, uv_time = fetch_latest_feed_value(UV_LIGHT_FEED_URL)
    return {
        "moisture": moisture,
        "moisture_time": moisture_time,
        "temperature": temperature,
        "temperature_time": temperature_time,
        "ambient_light": ambient_light,
        "ambient_time": ambient_time,
        "uv_light": uv_light,
        "uv_time": uv_time,
    }

def analyze_plant_health(sensor_data):
    try:
        moisture = int(sensor_data["moisture"]) if sensor_data["moisture"] is not None else None
        temperature = int(sensor_data["temperature"]) if sensor_data["temperature"] is not None else None
        ambient_light = int(sensor_data["ambient_light"]) if sensor_data["ambient_light"] is not None else None
        uv_light = int(sensor_data["uv_light"]) if sensor_data["uv_light"] is not None else None
    except Exception:
        return "Sorry, I couldn't interpret the sensor data.", "Please check your sensor setup."

    moisture_advice = ""
    if moisture is None:
        moisture_advice = "Moisture data unavailable."
    elif moisture <= 50:
        moisture_advice = "Soil is dry. Water your plant! \n Get to at least 750 on the moisture scale."
    elif 750 <= moisture <= 950:
        moisture_advice = "Soil moisture is good. No need to water now. \n Keep it at 750-950 on the moisture scale."
    else:
        moisture_advice = "Soil is too wet. Hold off on watering. \n Keep it at 750-950 on the moisture scale."

    temperature_advice = ""
    if temperature is None:
        temperature_advice = "Temperature data unavailable."
    elif temperature < 60:
        temperature_advice = "It's a bit cold for most houseplants. \n Consider moving to a warmer spot. (60-80°F)"
    elif 60 <= temperature <= 80:
        temperature_advice = "Temperature is ideal for most houseplants. \n (60-80°F)"
    else:
        temperature_advice = "It's quite warm. \n Make sure your plant isn't in direct sunlight for too long. (60-80°F)"

    ambient_light_advice = ""
    if ambient_light is None:
        ambient_light_advice = "Ambient light data unavailable."
    elif ambient_light < 1500:
        ambient_light_advice = "Light levels are low. \n Consider moving your plant closer to a window or adding a grow light. (1500-75000)"
    elif 1500 <= ambient_light <= 75000:
        ambient_light_advice = "Ambient light levels are ideal for most houseplants. \n (1500-75000)"
    else:
        ambient_light_advice = "Light levels are very high. \n Make sure your plant isn't getting too much direct sunlight. (1500-75000)"

    uv_light_advice = ""
    if uv_light is None:
        uv_light_advice = "UV light data unavailable."
    elif uv_light < 50:
        uv_light_advice = "UV levels are low. \n Your plant might benefit from more natural sunlight. (50-300)"
    elif 50 <= uv_light <= 300:
        uv_light_advice = "UV light levels are ideal for plant growth. \n (50-300)"
    else:
        uv_light_advice = "UV levels are very high. \n Consider providing some shade to protect your plant. (50-300)"

    summary = (
        f"Current soil moisture: {sensor_data['moisture']} (measured at {sensor_data['moisture_time']})\n\n"
        f"Current temperature: {sensor_data['temperature']}°F (measured at {sensor_data['temperature_time']})\n\n"
        f"Current ambient light: {sensor_data['ambient_light']} (measured at {sensor_data['ambient_time']})\n\n"
        f"Current UV light: {sensor_data['uv_light']} (measured at {sensor_data['uv_time']})\n\n"
        )
    advice = (
        f"Moisture advice: {moisture_advice}\n\n"
        f"Temperature advice: {temperature_advice}\n\n"
        f"Ambient light advice: {ambient_light_advice}\n\n"
        f"UV light advice: {uv_light_advice}"
        )
    return summary, advice

def ask_ollama(user_message, plant_summary="", plant_advice=""):
    try:
        context = ""
        if plant_summary and plant_advice:
            context = f"Here is the latest plant data:\n{plant_summary}\nAdvice: {plant_advice}\n"

        prompt = (
            f"You are a friendly plant care assistant. {context}"
            f"User: {user_message}\n"
            f"Respond as a helpful plant care expert in 2-5 sentences"
        )

        models_to_try = [
            "llama3.2:latest",
            "llama3.2",
            "llama2:latest",
        ]
        for model in models_to_try:
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 150,
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', 'Sorry,  I could not generate a response.')
                elif response.status_code == 404:
                    continue
                else:
                    continue
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                continue
        return "Sorry, none of the available models could generate a response. Try downloading a model with 'ollama pull llama2:3b'"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)."
    except Exception as e:
        return f"Sorry, I couldn't get a response: {str(e)}"

# --- Web UI ---

HOME_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Plant Adviser Web</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f6fff6; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #cce5cc; padding: 30px; }
        h1 { color: #2e7d32; }
        .nav { margin-bottom: 20px; }
        .nav a { 
            margin-right: 20px; 
            color: #fff; 
            text-decoration: none; 
            font-weight: bold; 
            font-size: 14px;
            background: #388e3c; 
            padding: 8px 16px; 
            border-radius: 8px; 
            border: 2px solid #000; 
            display: inline-block;
        }
        .nav a:hover { 
            background: #2e7d32; 
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }
        .footer { margin-top: 40px; color: #888; font-size: 0.9em; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 Plant Adviser Web</h1>
        <div class="nav">
            <a href="/status">Status</a>
            <a href="/chat">AI Chat</a>
        </div>
        <h2>Welcome!</h2>
        <p>Check your plant's health or chat with the AI for care advice.</p>
    </div>
    <div class="footer">Powered by Ollama & Adafruit IO</div>
</body>
</html>
'''

STATUS_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Plant Status</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f6fff6; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #cce5cc; padding: 30px; }
        h1 { color: #2e7d32; }
        pre { background: #f0f8f0; padding: 15px; border-radius: 6px; }
        .advice { background: #e8f5e9; padding: 15px; border-radius: 6px; margin-top: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { 
            margin-right: 20px; 
            color: #fff; 
            text-decoration: none; 
            font-weight: bold; 
            font-size: 14px;
            background: #388e3c; 
            padding: 8px 16px; 
            border-radius: 8px; 
            border: 2px solid #000; 
            display: inline-block;
        }
        .nav a:hover { 
            background: #2e7d32; 
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }
        .footer { margin-top: 40px; color: #888; font-size: 0.9em; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 Plant Status</h1>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/chat">AI Chat</a>
        </div>
        <h2>Current Plant Data</h2>
        <pre>{{ summary }}</pre>
        <div class="advice">
            <h3>Care Advice</h3>
            <pre>{{ advice }}</pre>
        </div>
    </div>
    <div class="footer">Powered by Ollama & Adafruit IO</div>
</body>
</html>
'''

CHAT_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Plant Chat</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f6fff6; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #cce5cc; padding: 30px; }
        h1 { color: #2e7d32; }
        .nav { margin-bottom: 20px; }
        .nav a { 
            margin-right: 20px; 
            color: #fff; 
            text-decoration: none; 
            font-weight: bold; 
            font-size: 14px;
            background: #388e3c; 
            padding: 8px 16px; 
            border-radius: 8px; 
            border: 2px solid #000; 
            display: inline-block;
        }
        .nav a:hover { 
            background: #2e7d32; 
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }
        .chat-box { background: #f0f8f0; padding: 15px; border-radius: 6px; min-height: 120px; margin-bottom: 20px; }
        .user-msg { color: #1565c0; }
        .ai-msg { color: #2e7d32; }
        .timestamp { color: #888; font-size: 0.8em; float: right; }
        .message-header { overflow: hidden; margin-bottom: 5px; }
        .tip { color: #666; font-size: 0.85em; font-style: italic; margin-top: 10px; text-align: center; }
        .footer { margin-top: 40px; color: #888; font-size: 0.9em; text-align: center; }
        form { display: flex; gap: 10px; }
        input[type=text] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #bdbdbd; }
        button { padding: 10px 18px; border-radius: 5px; border: none; background: #388e3c; color: #fff; font-weight: bold; cursor: pointer; }
        button:hover { background: #2e7d32; }
        #sending { display: none; color: #888; margin-top: 10px; }
    </style>
    <script>
        function showSending() {
            document.getElementById('sending').style.display = 'block';
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🌱 AI Plant Chat</h1>
        <div class="nav">
            <a href="/">Home</a>
            <a href="/status">Status</a>
        </div>
        <div class="chat-box">
            {% if chat_history %}
                {% for msg in chat_history %}
                    <div class="message-header">
                        <span class="timestamp">{{ msg['timestamp'] }}</span>
                    </div>
                    <div class="user-msg"><b>You:</b> {{ msg['user'] }}</div>
                    <div class="ai-msg"><b>AI:</b> {{ msg['ai'] }}</div>
                    <hr/>
                {% endfor %}
            {% else %}
                <em>Start chatting with the AI about your plant care!</em>
            {% endif %}
        </div>
        <form method="post" onsubmit="showSending()">
            <input type="text" name="user_input" placeholder="Ask about plant care..." autocomplete="off" required />
            <button type="submit">Send</button>
        </form>
        <div id="sending">Sending.. (around 30 seconds)</div>
        <div class="tip">💡 Tip: If it times out, try asking a simpler question first.</div>
    </div>
    <div class="footer">Powered by Ollama & Adafruit IO</div>
</body>
</html>
'''

@app.route("/")
def home():
    return render_template_string(HOME_PAGE)

@app.route("/status")
def status():
    sensor_data = get_latest_sensor_data()
    summary, advice = analyze_plant_health(sensor_data)
    return render_template_string(STATUS_PAGE, summary=summary, advice=advice)

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if 'chat_history' not in session:
        session['chat_history'] = []
    chat_history = session['chat_history']

    # Get current plant data for context
    sensor_data = get_latest_sensor_data()
    summary, advice = analyze_plant_health(sensor_data)

    if request.method == "POST":
        user_input = request.form.get("user_input", "").strip()
        if user_input:
            ai_response = ask_ollama(user_input, summary, advice)
            timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
            chat_history.append({
                'user': user_input, 
                'ai': ai_response, 
                'timestamp': timestamp
            })
            session['chat_history'] = chat_history
            return redirect(url_for('chat'))
    return render_template_string(CHAT_PAGE, chat_history=chat_history)

if __name__ == "__main__":
    print("🌱 Plant Adviser Web Server Starting...")
    print("=" * 50)
    print("🌐 Open your web browser and go to:")
    print("   http://localhost:5000")
    print("=" * 50)
    print("💡 Make sure Ollama is running for AI chat features!")
    print("   Run: ollama serve")
    print("=" * 50)
    app.run(debug=True, port=5000) 
