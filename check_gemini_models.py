"""Script to check available Gemini models"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] GEMINI_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("Checking available Gemini models...\n")

try:
    models = genai.list_models()
    
    print("Available models:")
    print("=" * 60)
    
    generate_content_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.split('/')[-1] if '/' in model.name else model.name
            generate_content_models.append(model_name)
            print(f"[OK] {model_name}")
            print(f"   Full name: {model.name}")
            print(f"   Methods: {', '.join(model.supported_generation_methods)}")
            print()
    
    if generate_content_models:
        print("=" * 60)
        print(f"\n[SUCCESS] Found {len(generate_content_models)} model(s) with generateContent support")
        print(f"\nRecommended model to use: {generate_content_models[0]}")
        print(f"\nAdd this to your .env file:")
        print(f"GEMINI_MODEL={generate_content_models[0]}")
    else:
        print("[ERROR] No models with generateContent method found")
        print("\nPlease check:")
        print("1. Your API key is valid")
        print("2. Your API key has access to Gemini models")
        print("3. You're using the correct API endpoint")
        
except Exception as e:
    print(f"[ERROR] Error listing models: {str(e)}")
    print("\nPlease check:")
    print("1. Your API key is correct")
    print("2. You have internet connection")
    print("3. The google-generativeai package is installed correctly")

