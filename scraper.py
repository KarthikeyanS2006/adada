import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"

# Your NVIDIA API Key
NVIDIA_API_KEY = "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"

# Using the Kimi K2.5 model from your list
MODEL_NAME = "moonshotai/kimi-k2.5"

# Initialize the NVIDIA NIM Client
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=NVIDIA_API_KEY
)

def process_with_ai(raw_text, filename):
    """Sends text to NVIDIA NIM and returns a structured JSON object."""
    prompt = f"""
    Task: Convert the provided exam paper text into a clean JSON object.
    Language: The 'tanglish' field must be Tamil in English script.
    
    JSON Structure:
    {{
      "document_info": {{ "exam_name": "{filename}" }},
      "archive_data": [
        {{
          "q_number": 1,
          "question_text": "...",
          "options": [
            {{ "id": "1", "text": "...", "is_correct": true }},
            {{ "id": "2", "text": "...", "is_correct": false }}
          ],
          "explanation": {{ 
            "english": "logic in English", 
            "tanglish": "logic in Tanglish" 
          }}
        }}
      ]
    }}
    
    Exam Text:
    {raw_text[:4000]}
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a technical assistant that outputs ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            # NVIDIA NIM supports response_format for structured output
            response_format={"type": "json_object"}
        )
        
        text_content = response.choices[0].message.content.strip()
        return json.loads(text_content)
        
    except Exception as e:
        print(f"NVIDIA API Error for {filename}: {e}")
        return None

def full_pipeline():
    """Main function to walk through the archive and process PDFs."""
    if not os.path.exists(BASE_DIR):
        print(f"Error: Folder '{BASE_DIR}' not found.")
        return

    print(f"--- Starting NVIDIA NIM Pipeline: {MODEL_NAME} ---")
    
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                if os.path.exists(json_path):
                    continue

                print(f"Processing: {file}")
                
                try:
                    doc = fitz.open(pdf_path)
                    extracted_text = ""
                    # Reading first 3 pages
                    for page in doc[:3]:
                        extracted_text += page.get_text()
                    
                    if not extracted_text.strip():
                        continue

                    json_data = process_with_ai(extracted_text, file)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Saved JSON successfully.")
                        
                        # NVIDIA NIM Free tier is usually generous, 1s delay is enough
                        time.sleep(1) 
                    else:
                        print(f"AI failed to return JSON for {file}.")

                except Exception as e:
                    print(f"System Error: {e}")

if __name__ == "__main__":
    full_pipeline()
