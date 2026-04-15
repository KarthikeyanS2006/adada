import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration
TARGET_URLS = ["https://www.adda247.com/jobs/previous-year-question-papers/", "https://www.adda247.com/jobs/previous-year-question-papers/","https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/","https://www.adda247.com/jobs/ssc-chsl-previous-year-question-paper/","https://www.adda247.com/jobs/ssc-cgl-previous-year-question-paper/","https://www.adda247.com/jobs/ssc-mts-previous-year-question-paper/","https://www.adda247.com/jobs/ssc-jht-previous-year-question-paper/","https://www.adda247.com/jobs/ssc-cpo-previous-year-question-paper/",]
DOWNLOAD_DIR = "SSC"
BATCH_SIZE = 50

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_pdfs():
    count = 0
    for url in TARGET_URLS:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf'):
                pdf_url = urljoin(url, href)
                pdf_name = os.path.join(DOWNLOAD_DIR, href.split('/')[-1])
                
                if not os.path.exists(pdf_name):
                    print(f"Downloading: {pdf_url}")
                    r = requests.get(pdf_url)
                    with open(pdf_name, 'wb') as f:
                        f.write(r.content)
                    count += 1
                
                # Stop if batch limit reached
                if count >= BATCH_SIZE:
                    print(f"Reached batch limit of {BATCH_SIZE}")
                    return

download_pdfs()
