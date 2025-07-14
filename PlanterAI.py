#######################
# Pet Planter AI Code #
#######################

import requests
import json

# URLs for Adafruit IO feeds
MOISTURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/moisture/data?limit=1"
TEMPERATURE_FEED_URL = "https://io.adafruit.com/api/v2/abinandp/feeds/temperature/data?limit=1"

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
    """Fetch the latest moisture and temperature values."""
    moisture, moisture_time = fetch_latest_feed_value(MOISTURE_FEED_URL)
    temperature, temperature_time = fetch_latest_feed_value(TEMPERATURE_FEED_URL)
    return {
        "moisture": moisture,
        "moisture_time": moisture_time,
        "temperature": temperature,
        "temperature_time": temperature_time,
    }

def analyze_plant_health(sensor_data):
    """Analyze sensor data and return a health summary and care advice."""
    try:
        moisture = int(sensor_data["moisture"]) if sensor_data["moisture"] is not None else None
        temperature = int(sensor_data["temperature"]) if sensor_data["temperature"] is not None else None
    except Exception:
        return "Sorry, I couldn't interpret the sensor data.", "Please check your sensor setup."

    # Updated thresholds based on your sensor
    moisture_advice = ""
    if moisture is None:
        moisture_advice = "Moisture data unavailable."
    elif moisture <= 349:
        moisture_advice = "Soil is very dry. Water your plant! Get to at least 450 on the moisture scale."
    elif 450 <= moisture <= 500:
        moisture_advice = "Soil moisture is good. No need to water now. Keep it at 450-500 on the moisture scale."
    else:
        moisture_advice = "Soil is too wet. Hold off on watering."

    temperature_advice = ""
    if temperature is None:
        temperature_advice = "Temperature data unavailable."
    elif temperature < 60:
        temperature_advice = "It's a bit cold for most houseplants. Consider moving to a warmer spot."
    elif 60 <= temperature <= 80:
        temperature_advice = "Temperature is ideal for most houseplants."
    else:
        temperature_advice = "It's quite warm. Make sure your plant isn't in direct sunlight for too long."

    summary = (
        f"Current soil moisture: {sensor_data['moisture']} (measured at {sensor_data['moisture_time']})\n"
        f"Current temperature: {sensor_data['temperature']}°F (measured at {sensor_data['temperature_time']})"
    )
    advice = f"Moisture advice: {moisture_advice}\nTemperature advice: {temperature_advice}"
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
                    timeout=15  # Shorter timeout for faster response
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', 'Sorry, I could not generate a response.')
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

        elif user_input in ["status", "health", "how is my plant?"]:
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
    print("Plant Adviser with Ollama AI")
    print("To use AI chat:")
    print("1. Start Ollama server: ollama serve")
    print("2. In another terminal, run: ollama run llama3.2")
    print("3. Or download llama3.2: ollama pull llama3.2")
    print("4. Then run this script: python plantadviser_ollama.py")
    print("-" * 50)
    chat_loop()
