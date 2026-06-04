import os
import requests
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from backend.config import settings
    gemini_key = settings.GEMINI_API_KEY
except Exception as e:
    print(f"Warning: Could not import backend.config settings: {e}")
    gemini_key = os.environ.get("GEMINI_API_KEY")

def test_gemini():
    # If key is empty in settings, check environment variable directly
    key = gemini_key or os.environ.get("GEMINI_API_KEY")
    
    if not key:
        print("ERROR: GEMINI_API_KEY is not set in your .env file or environment.")
        print("Please add 'GEMINI_API_KEY=your_actual_api_key' to your .env file in the project root.")
        sys.exit(1)
        
    print(f"Found API key: {key[:6]}...{key[-4:] if len(key) > 10 else ''}")
    print("Testing connection to Gemini API...")
    
    # Use standard endpoint and model
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Explain what a Melakarta raga is in Carnatic music in 2 sentences."
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            try:
                answer = data['candidates'][0]['content']['parts'][0]['text']
                print("\nSuccess! Response from Gemini:")
                print("-" * 50)
                print(answer.strip())
                print("-" * 50)
            except (KeyError, IndexError) as err:
                print(f"Error parsing response: {err}")
                print(f"Raw response: {data}")
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Details: {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_gemini()
