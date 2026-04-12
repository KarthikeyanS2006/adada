import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Only focusing on Adda247 as requested
TARGET_SITE = "https://www.adda247.com/jobs/previous-year-question-papers/"
BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 80 

def organize_file(filename):
    # Extract year from filename
    year_match = re.search(r'20[0-2][0-9]', filename)
    year = year_match.group(0) if year_match else "Misc_Year"
    
    # Categorize by exam type
    fn_upper = filename.upper()
    if "PRELIM" in fn_upper:
        exam_type = "Prelims"
    elif "MAIN" in fn_upper:
        exam_type = "Mains"
    else:
        exam_type = "Study_Material"

    target_path = os.path.join(BASE_DIR, "Adda247", year, exam_type)
    os.makedirs(target_path, exist_ok=True)
    return target_path

def download_batch():
    # Modern browser headers to prevent blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.adda247.com/'
    }
    
    download_count = 0
    os.makedirs(BASE_DIR, exist_ok=True)

    print(f"--- Starting Full Scan of Adda247 ---")
    try:
        response = requests.get(TARGET_SITE, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finding all anchor tags
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} total links. Checking for PDFs...")

        for link in links:
            if download_count >= BATCH_LIMIT:
                print(f"Reached batch limit of {BATCH_LIMIT}. Stopping run.")
                return

            href = link['href']
            # Clean up URLs and check for PDF extension
            if href.lower().split('?')[0].endswith('.pdf'):
                pdf_url = urljoin(TARGET_SITE, href)
                file_name = pdf_url.split('/')[-1].split('?')[0]
                
                target_dir = organize_file(file_name)
                final_path = os.path.join(target_dir, file_name)

                if not os.path.exists(final_path):
                    print(f"[{download_count+1}/{BATCH_LIMIT}] Downloading: {file_name}")
                    try:
                        pdf_res = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                        if pdf_res.status_code == 200:
                            with open(final_path, 'wb') as f:
                                for chunk in pdf_res.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            download_count += 1
                    except Exception as e:
                        print(f"Error downloading {file_name}: {e}")
        
        if download_count == 0:
            print("No new files found to download.")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    download_batch()
