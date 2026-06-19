"""
Test script to check Gemini API key and available models
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"API Key found: {api_key[:10]}...")

# Configure API
genai.configure(api_key=api_key)

# List available models
print("\nAvailable models:")
try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
except Exception as e:
    print(f"ERROR listing models: {str(e)}")
    exit(1)

# Test with a simple prompt
print("\nTesting content generation...")
try:
    # Try gemini-1.5-flash first
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello in one sentence")
    print(f"SUCCESS! Response: {response.text}")
except Exception as e:
    print(f"ERROR with gemini-1.5-flash: {str(e)}")
    
    # Try gemini-pro as fallback
    try:
        print("\nTrying gemini-pro...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say hello in one sentence")
        print(f"SUCCESS! Response: {response.text}")
    except Exception as e2:
        print(f"ERROR with gemini-pro: {str(e2)}")
