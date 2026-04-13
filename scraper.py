import os
import json
import time
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
API_KEYS = [
    "AIzaSyDKjnVYKIUb9Cg2odXQU5aaQhkldu7e9Kc",
    "AIzaSyChGoGU6QGFFrmbodka8i7cGfMG2xVWeLE"
]
current_key_index = 0

def rotate_key():
    """Switches to the next API key in the list to avoid rate limits."""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"\n--- Switched to API Key {current_key_index} ---")

def process_with_ai(raw_text, filename):
    """Sends extracted text to Gemini and returns structured JSON."""
    global current_key_index
    
    # Configure with the current rotating key
    genai.configure(api_key=API_KEYS[current_key_index])
    
    # Using stable gemini-1.5-flash
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
    
    prompt = f"""
    Return ONLY a JSON object for this exam paper text.
    Include Question text, Options, Correct Answer, English Explanation, and Tanglish Explanation.
    
    Rules:
    1. 'tanglish' should be Tamil concepts written in English script.
    2. Ensure the JSON is valid and follows this exact structure:
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
    
    try:
        # RequestOptions forces the stable 'v1' API version to avoid 404/v1beta issues
        response = model.generate_content(
            prompt,
            request_options=RequestOptions(api_version='v1')
        )
        
        text_content = response.text
        
        # Strip Markdown code blocks if present
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
    """Scans the archive, extracts text from PDFs, and saves JSON results."""
    if not os.path.exists(BASE_DIR):
        print(f"Error: Directory '{BASE_DIR}' not found.")
        return

    print(f"--- Starting Pipeline in {BASE_DIR} ---")
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                # Skip if already processed to save API quota
                if os.path.exists(json_path):
                    continue

                print(f"\n[Processing]: {file}")
                
                try:
                    # Open PDF and extract text from the first 3 pages
                    doc = fitz.open(pdf_path)
                    extracted_text = ""
                    for page in doc[:3]:
                        extracted_text += page.get_text()
                    
                    if not extracted_text.strip():
                        print(f"Skipping {file}: No text found (likely scanned images).")
                        continue

                    # Process with AI
                    json_data = process_with_ai(extracted_text, file)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Successfully saved: {os.path.basename(json_path)}")
                        
                        # Wait 2 seconds to respect rate limits
                        time.sleep(2)
                    else:
                        print(f"Could not generate JSON for {file}.")

                except Exception as e:
                    print(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    full_pipeline()
