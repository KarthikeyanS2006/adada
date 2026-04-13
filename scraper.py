import os
import json
import time
import fitz  # PyMuPDF
from google import genai

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
API_KEYS = [
    "AIzaSyDKjnVYKIUb9Cg2odXQU5aaQhkldu7e9Kc",
    "AIzaSyChGoGU6QGFFrmbodka8i7cGfMG2xVWeLE"
]
current_key_index = 0

def get_client():
    global current_key_index
    return genai.Client(api_key=API_KEYS[current_key_index])

def rotate_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"\n--- Switched to API Key {current_key_index} ---")

def process_with_ai(raw_text, filename):
    client = get_client()
    
    prompt = f"""
    Return ONLY a JSON object for this exam paper.
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
    Text: {raw_text[:3500]}
    """
    
    try:
        # The new SDK uses 'models.generate_content' differently
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        text_content = response.text
        if "```json" in text_content:
            text_content = text_content.split("```json")[1].split("```")[0]
        elif "```" in text_content:
            text_content = text_content.split("```")[1].split("```")[0]
            
        return json.loads(text_content.strip())
        
    except Exception as e:
        print(f"Key {current_key_index} Error: {e}")
        rotate_key()
        return None

def full_pipeline():
    if not os.path.exists(BASE_DIR):
        print(f"Folder {BASE_DIR} not found.")
        return

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                if os.path.exists(json_path): continue

                print(f"Processing: {file}")
                try:
                    doc = fitz.open(pdf_path)
                    text = "".join([page.get_text() for page in doc[:3]])
                    
                    if not text.strip(): continue

                    data = process_with_ai(text, file)
                    if data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print("Saved.")
                        time.sleep(1)
                except Exception as e:
                    print(f"Skip {file}: {e}")

if __name__ == "__main__":
    full_pipeline()
