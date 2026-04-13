import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI

# --- CONFIGURATION ---
BASE_DIR = "Longinsent_Archive"
# Your OpenRouter API Key
OPENROUTER_API_KEY = "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"
# The specific Gemma model you requested
MODEL_NAME = "google/gemma-4-31b-it:free"

# Initialize the OpenRouter Client
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

def process_with_ai(raw_text, filename):
    """Sends text to OpenRouter and returns a structured JSON object."""
    prompt = f"""
    Task: Convert the provided exam paper text into a clean JSON object.
    Language Requirement: The 'tanglish' field must contain Tamil explanations written in English script.
    
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
            "english": "Detailed logic in English", 
            "tanglish": "Detailed logic in Tanglish" 
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
                {"role": "system", "content": "You are a JSON-only technical assistant. Do not include conversational text or markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            # Note: response_format is used to ensure the model behaves like a JSON API
            response_format={"type": "json_object"}
        )
        
        text_content = response.choices[0].message.content.strip()
        
        # In case the model still includes markdown triple backticks
        if "```json" in text_content:
            text_content = text_content.split("```json")[1].split("```")[0]
        elif "```" in text_content:
            text_content = text_content.split("```")[1].split("```")[0]
            
        return json.loads(text_content)
        
    except Exception as e:
        print(f"OpenRouter Error while processing {filename}: {e}")
        return None

def full_pipeline():
    """Main function to walk through the archive and process PDFs."""
    if not os.path.exists(BASE_DIR):
        print(f"Error: The folder '{BASE_DIR}' was not found in the repository.")
        return

    print(f"--- Starting Pipeline: Processing PDFs with {MODEL_NAME} ---")
    
    # Walk through all folders inside the archive
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                json_path = pdf_path.replace(".pdf", ".json")

                # Skip if the JSON already exists (saves credits/time)
                if os.path.exists(json_path):
                    continue

                print(f"Processing: {file}")
                
                try:
                    # Open the PDF and extract text from the first few pages
                    doc = fitz.open(pdf_path)
                    extracted_text = ""
                    # Reading 4 pages to give the AI enough context for questions
                    for page in doc[:4]:
                        extracted_text += page.get_text()
                    
                    if not extracted_text.strip():
                        print(f"Skipped {file}: No readable text found.")
                        continue

                    # Send to OpenRouter
                    json_data = process_with_ai(extracted_text, file)
                    
                    if json_data:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"Successfully saved JSON.")
                        
                        # Wait for the free tier rate limit (approx 10-15 requests per minute)
                        time.sleep(6) 
                    else:
                        print(f"AI failed to return valid JSON for {file}.")

                except Exception as e:
                    print(f"System Error processing {file}: {e}")

if __name__ == "__main__":
    full_pipeline()
