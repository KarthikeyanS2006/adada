import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URLs organized by exam type
TARGET_URLS = [
    "https://www.adda247.com/jobs/previous-year-question-papers/",
    "https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/",
    "https://www.adda247.com/jobs/ssc-chsl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cgl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-mts-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-jht-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cpo-previous-year-question-paper/"
]

BATCH_SIZE = 80

def get_folder_name(url):
    """Determines folder name based on the URL structure."""
    if "ssc-gd" in url: return "SSC_GD"
    if "ssc-chsl" in url: return "SSC_CHSL"
    if "ssc-cgl" in url: return "SSC_CGL"
    if "ssc-mts" in url: return "SSC_MTS"
    if "ssc-jht" in url: return "SSC_JHT"
    if "ssc-cpo" in url: return "SSC_CPO"
    return "General_Papers"

def download_pdfs():
    count = 0
    
    for url in TARGET_URLS:
        folder_name = get_folder_name(url)
        # Create folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        print(f"Checking URL: {url} (Saving to: {folder_name})")
        
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if href.endswith('.pdf'):
                    pdf_url = urljoin(url, href)
                    file_name = href.split('/')[-1]
                    # Clean up filename (remove queries)
                    file_name = file_name.split('?')[0]
                    
                    pdf_path = os.path.join(folder_name, file_name)
                    
                    # Skip if file already exists in the repo
                    if not os.path.exists(pdf_path):
                        print(f"  Downloading [{count+1}/{BATCH_SIZE}]: {file_name}")
                        try:
                            r = requests.get(pdf_url, timeout=20)
                            with open(pdf_path, 'wb') as f:
                                f.write(r.content)
                            count += 1
                        except Exception as e:
                            print(f"  Failed to download {file_name}: {e}")
                    
                    # Stop strictly at 50
                    if count >= BATCH_SIZE:
                        print(f"\nSUCCESS: Reached batch limit of {BATCH_SIZE} files.")
                        return
        except Exception as e:
            print(f"Error accessing {url}: {e}")

if __name__ == "__main__":
    download_pdfs()
