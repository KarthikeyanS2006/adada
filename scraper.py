import os
import json
import time
import requests
import fitz  # PyMuPDF
import google.generativeai as genai

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
API_KEYS = [
    "AIzaSyDKjnVYKIUb9Cg2odXQU5aaQhkldu7e9Kc",
    "AIzaSyChGoGU6QGFFrmbodka8i7cGfMG2xVWeLE"
]
current_key_index = 0

def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"\n--- Switched to API Key {current_key_index} ---")

def process_with_ai(raw_text, filename):
    global current_key_index
    genai.configure(api_key=API_KEYS[current_key_index])
    
    # Based on the API reference you provided:
    # We must use the 'models/' prefix for the resource name.
    model_names = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest']
    
    for m_name in model_names:
        try:
            print(f"Trying model: {m_name}...")
            model = genai.GenerativeModel(model_name=m_name)
            
            prompt = f"""
            Task: Convert exam text to structured JSON.
            Explanations: Provide logic in English and Tanglish.
            Format:
            {{
              "document_info": {{ "exam_name": "{filename}" }},
              "archive_data": [
                {{
                  "q_number": 1,
                  "question_text": "...",
                  "options": [{{ "id": "1", "text": "...", "is_correct": true }}],
                  "explanation": {{ "english": "...", "tanglish": "..." }}
                }}
              ]
            }}
            Text: {raw_text[:3000]}
            """
            
            response = model.generate_content(prompt)
            
            if not response.text:
                continue

            text_content = response.text
            # Clean JSON formatting
            if "```json" in text_content:
                text_content = text_content.split("```json")[1].split("```")[0]
            elif "```" in text_content:
                text_content = text_content.split("```")[1].split("```")[0]
            
            return json.loads(text_content.strip())
                
        except Exception as e:
            print(f"Model {m_name} failed: {e}")
            continue 
            
    rotate_key()
    return None

def full_pipeline():
    if not os.path.exists(BASE_DIR):
        print(f"Error: {BASE_DIR} not found.")
        return

    print("--- Starting Longinset Archive Processor ---")
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                if os.path.exists(json_path):
                    continue

                print(f"\n[Processing]: {file}")
                
                try:
                    doc = fitz.open(pdf_path)
                    extracted_text = ""
                    # Grab only first 2 pages to ensure we don't hit token limits during testing
                    for page in doc[:2]:
                        extracted_text += page.get_text()
                    
                    if not extracted_text.strip():
                        print("No text found.")
                        continue

                    json_data = process_with_ai(extracted_text, file)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Saved JSON successfully.")
                        time.sleep(2) 
                    else:
                        print("AI could not generate JSON.")
                except Exception as e:
                    print(f"System Error: {e}")

if __name__ == "__main__":
    full_pipeline()
