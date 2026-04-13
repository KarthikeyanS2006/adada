import os
import json
import time
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
# Rotating between your provided keys
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
    
    # Using 'gemini-1.5-flash-latest' to resolve the 404 version error
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""
    Extract the questions from this exam text and convert them into a valid JSON object.
    
    Rules:
    1. Identify Question text, Options, and the Correct Answer.
    2. Provide an explanation in English.
    3. Provide a 'Tanglish' explanation (Tamil concepts in English script).
    4. If the answer isn't clear, mark 'is_correct' based on your knowledge.
    
    Format:
    {{
      "document_info": {{
        "exam_name": "{filename}",
        "processed_date": "2026-04-13"
      }},
      "archive_data": [
        {{
          "q_number": 1,
          "question_text": "...",
          "options": [
            {{ "id": "1", "text": "...", "is_correct": false }},
            {{ "id": "2", "text": "...", "is_correct": true }}
          ],
          "explanation": {{
            "english": "...",
            "tanglish": "..."
          }}
        }}
      ]
    }}

    Text Content:
    {raw_text[:4000]}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for strict JSON
            )
        )
        
        # Clean the AI response (remove markdown code blocks)
        text_content = response.text
        if "```json" in text_content:
            text_content = text_content.split("```json")[1].split("```")[0]
        elif "```" in text_content:
            text_content = text_content.split("```")[1].split("```")[0]
            
        return json.loads(text_content.strip())
        
    except Exception as e:
        print(f"Error with Key {current_key_index}: {e}")
        rotate_key()
        return None

def full_pipeline():
    if not os.path.exists(BASE_DIR):
        print(f"Error: {BASE_DIR} folder not found.")
        return

    print("--- Starting Longinset Archive Processor ---")
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                # Skip files already processed to save API quota
                if os.path.exists(json_path):
                    continue

                print(f"\n[Processing PDF]: {file}")
                
                try:
                    # 1. Extract Text from first few pages
                    doc = fitz.open(pdf_path)
                    extracted_text = ""
                    # Reading first 5 pages to stay within token limits
                    for page in doc[:5]:
                        extracted_text += page.get_text()
                    
                    if not extracted_text.strip():
                        print(f"No text found in {file} (might be a scanned image).")
                        continue

                    # 2. Get AI processed JSON
                    json_data = process_with_ai(extracted_text, file)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Successfully saved: {os.path.basename(json_path)}")
                        
                        # Small delay to avoid rate limiting
                        time.sleep(1)
                    else:
                        print(f"Skipping {file} due to AI error.")

                except Exception as e:
                    print(f"Failed to handle {file}: {e}")

if __name__ == "__main__":
    full_pipeline()
