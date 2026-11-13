"""
Tessalynt - Gemini API Connection Diagnostic Script
Verifies your GEMINI_API_KEY from .env and tests model availability.
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key or api_key == "your_new_api_key":
    print("[ERROR] Please set a valid GEMINI_API_KEY in your .env file.")
    exit(1)

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    print("[INFO] Attempting to connect to Gemini API...")
    # Try preferred models
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    success = False
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Respond with 'Tessalynt AI connection verified successfully.'")
            print(f"[SUCCESS] Model '{model_name}' responded:\n{response.text.strip()}")
            success = True
            break
        except Exception as me:
            print(f"[WARN] Model '{model_name}' unavailable: {me}")
            
    if not success:
        print("[ERROR] Could not generate content with any tested model.")
except Exception as e:
    print(f"[ERROR] API Connection failed: {e}")
