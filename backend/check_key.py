from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

print(f"Key loaded: {bool(key)}")
if key:
    print(f"Key length: {len(key)}")
    try:
        genai.configure(api_key=key)
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"API Error: {e}")
else:
    print("No key found.")
