#######################
# Pet Planter AI Code #
#######################

import requests
import json

# URLs for Adafruit IO feeds
MOISTURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/moisture/data?limit=1"
TEMPERATURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/temperature/data?limit=1"
AMBIENT_LIGHT_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/ambient/data?limit=1"
UV_LIGHT_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/uv/data?limit=1"

def fetch_latest_feed_value(feed_url):
    """Fetch the latest value from an Adafruit IO feed."""
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
    """Fetch the latest moisture, temperature, ambient light, and UV values."""
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
    """Analyze sensor data and return a health summary and care advice."""
    try:
        moisture = int(sensor_data["moisture"]) if sensor_data["moisture"] is not None else None
        temperature = int(sensor_data["temperature"]) if sensor_data["temperature"] is not None else None
        ambient_light = int(sensor_data["ambient_light"]) if sensor_data["ambient_light"] is not None else None
        uv_light = int(sensor_data["uv_light"]) if sensor_data["uv_light"] is not None else None
    except Exception:
        return "Sorry, I couldn't interpret the sensor data.", "Please check your sensor setup."

    # Updated thresholds based on your sensor
    moisture_advice = ""
    if moisture is None:
        moisture_advice = "Moisture data unavailable."
    elif moisture <= 50:
        moisture_advice = "Soil is dry. Water your plant! Get to at least 750 on the moisture scale."
    elif 750 <= moisture <= 950:
        moisture_advice = "Soil moisture is good. No need to water now. Keep it at 750-950 on the moisture scale."
    else:
        moisture_advice = "Soil is too wet. Hold off on watering. Keep it at 750-950 on the moisture scale."

    temperature_advice = ""
    if temperature is None:
        temperature_advice = "Temperature data unavailable."
    elif temperature < 60: 
        temperature_advice = "It's a bit cold for most houseplants. Consider moving to a warmer spot. (60-80°F)"
    elif 60 <= temperature <= 80:
        temperature_advice = "Temperature is ideal for most houseplants. (60-80°F)"
    else:
        temperature_advice = "It's quite warm. Make sure your plant isn't in direct sunlight for too long. (60-80°F)"

    ambient_light_advice = ""
    if ambient_light is None:
        ambient_light_advice = "Ambient light data unavailable."
    elif ambient_light < 1500:
        ambient_light_advice = "Light levels are low. Consider moving your plant closer to a window or adding a grow light. (1500-75000)"
    elif 1500 <= ambient_light <= 75000:
        ambient_light_advice = "Ambient light levels are ideal for most houseplants. (1500-75000)"
    else:
        ambient_light_advice = "Light levels are very high. Make sure your plant isn't getting too much direct sunlight. (1500-75000)"

    uv_light_advice = ""
    if uv_light is None:
        uv_light_advice = "UV light data unavailable."
    elif uv_light < 50:
        uv_light_advice = "UV levels are low. Your plant might benefit from more natural sunlight. (50-300)"
    elif 50 <= uv_light <= 300:
        uv_light_advice = "UV light levels are ideal for plant growth. (50-300)"
    else:
        uv_light_advice = "UV levels are very high. Consider providing some shade to protect your plant. (50-300)"

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
    """Ask Ollama for plant care advice using a smaller model."""
    try:
        context = ""
        if plant_summary and plant_advice:
            context = f"Here is the latest plant data:\n{plant_summary}\nAdvice: {plant_advice}\n"

        prompt = (
            f"You are a friendly plant care assistant. {context}"
            f"User: {user_message}\n"
            f"Respond as a helpful plant care expert in 2-3 sentences."
        )

        # Try different smaller models in order of preference
        models_to_try = [
            "llama3.2:latest",         # Your preferred model
            "llama3.2",  # Alternative naming
            "llama2:latest",    # Fallback
        ]
        
        for model in models_to_try:
            try:
                print(f"Trying model: {model}...")
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 150,  # Limit response length
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=30  # Shorter timeout for faster response
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', 'Sorry,  I could not generate a response.')
                elif response.status_code == 404:
                    print(f"Model {model} not found, trying next...")
                    continue
                else:
                    print(f"Error with {model}: {response.status_code}")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"Timeout with {model}, trying next...")
                continue
            except Exception as e:
                print(f"Error with {model}: {e}")
                continue
        
        return "Sorry, none of the available models could generate a response. Try downloading a model with 'ollama pull llama2:3b'"
            
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)."
    except Exception as e:
        return f"Sorry, I couldn't get a response: {str(e)}"

def chat_loop():
    print("Welcome to your Plant Adviser!")
    print("Commands:")
    print("- 'status': Get your plant's health")
    print("- 'chat': Start chatting with AI about plant care")
    print("- 'quit': Exit the program")
    print("- 'back': Return to main menu")
    print("\nNote: For AI chat, make sure Ollama is running and you have a model downloaded.")

    while True:
        user_input = input("\nYou: ").strip().lower()

        if user_input in ["quit", "exit"]:
            print("Goodbye! Take care of your plant!")
            break

        elif user_input in ["status", "health", "how is my plant?", "how is my plant", "stats",]:
            sensor_data = get_latest_sensor_data()
            summary, advice = analyze_plant_health(sensor_data)
            print(f"\nPlant Adviser:\n{summary}\n{advice}\n")

        elif user_input in ["chat", "ai", "ollama"]:
            print("\n=== AI Plant Care Chat (Ollama) ===")
            print("You can now chat with AI about plant care!")
            print("Type 'back' to return to main menu, or 'quit' to exit.")

            # Get current plant data for context
            sensor_data = get_latest_sensor_data()
            summary, advice = analyze_plant_health(sensor_data)

            while True:
                chat_input = input("\nAI Chat: ").strip()

                if chat_input.lower() in ["back", "return", "exit"]:
                    print("Returning to main menu...")
                    break
                elif chat_input.lower() in ["quit"]:
                    print("Goodbye! Take care of your plant!")
                    exit()
                elif chat_input:
                    print("Thinking...")
                    response = ask_ollama(chat_input, summary, advice)
                    print(f"\nAI Assistant: {response}\n")
                else:
                    print("Please type something to chat with AI!")

        else:
            print("Plant Adviser: Available commands - 'status', 'back', 'chat', or 'quit'.")

if __name__ == "__main__":
    print("--------------------------------")
    print("- Plant Adviser with Ollama AI -")
    print("--------------------------------")
    print("To use AI chat:")
    print("1. Start Ollama server: ollama serve")
    print("2. In another terminal, run: ollama run llama3.2")
    print("3. Or download llama3.2: ollama pull llama3.2")
    print("4. Then run this script: python plantadviser_ollama.py")
    print("-" * 50)
    chat_loop()
