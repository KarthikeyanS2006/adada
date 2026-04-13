import os
import json
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
API_KEYS = [
    "AIzaSyDKjnVYKIUb9Cg2odXQU5aaQhkldu7e9Kc",
    "AIzaSyChGoGU6QGFFrmbodka8i7cGfMG2xVWeLE"
]
current_key_index = 0

def get_model():
    global current_key_index
    genai.configure(api_key=API_KEYS[current_key_index])
    return genai.GenerativeModel('gemini-1.5-flash')

def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"--- Switched to API Key {current_key_index} ---")

def process_with_ai(raw_text):
    model = get_model()
    prompt = f"""
    Convert this exam text into a JSON object. 
    Format:
    {{
      "document_info": {{ "exam_name": "Detect from text", "exam_year": 2024 }},
      "archive_data": [
        {{
          "q_number": 1,
          "question_text": "...",
          "options": [{{ "id": "1", "text": "...", "is_correct": true }}],
          "explanation": {{ "english": "...", "tanglish": "..." }}
        }}
      ]
    }}
    Text: {raw_text[:4000]} 
    """
    try:
        response = model.generate_content(prompt)
        # Clean JSON from markdown
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}. Rotating key...")
        rotate_key()
        return None

def full_pipeline():
    # Step 1: Walk through the repository
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                # Skip if already processed
                if os.path.exists(json_path):
                    continue

                print(f"Processing: {file}")
                
                # Step 2: Extract Text
                try:
                    doc = fitz.open(pdf_path)
                    full_text = ""
                    for page in doc[:3]: # Limit to first 3 pages to save tokens
                        full_text += page.get_text()
                    
                    # Step 3: AI Magic
                    json_data = process_with_ai(full_text)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Successfully created JSON for {file}")
                        time.sleep(2) # Prevent spamming
                except Exception as e:
                    print(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    full_pipeline()
