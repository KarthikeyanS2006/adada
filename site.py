import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuration
TARGET_URLS = [
    "https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/",
    "https://www.adda247.com/jobs/ssc-chsl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cgl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-mts-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-jht-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cpo-previous-year-question-paper/"
]
BATCH_SIZE = 50

def get_folder_name(url):
    for key in ['gd', 'chsl', 'cgl', 'mts', 'jht', 'cpo']:
        if key in url.lower():
            return f"SSC_{key.upper()}"
    return "General_Papers"

def download_pdfs():
    count = 0
    visited_pages = set()

    for start_url in TARGET_URLS:
        if count >= BATCH_SIZE: break
        
        folder_name = get_folder_name(start_url)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        print(f"Checking: {start_url}")
        try:
            res = requests.get(start_url, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Find all links on the page
            links = [urljoin(start_url, a['href']) for a in soup.find_all('a', href=True)]
            
            for link in links:
                if count >= BATCH_SIZE: return
                
                # 1. If it's a direct PDF
                if link.endswith('.pdf'):
                    file_name = link.split('/')[-1].split('?')[0]
                    path = os.path.join(folder_name, file_name)
                    
                    if not os.path.exists(path):
                        print(f"  Downloading: {file_name}")
                        r = requests.get(link)
                        with open(path, 'wb') as f:
                            f.write(r.content)
                        count += 1
                
                # 2. If it's a sub-page (article) that might have PDFs, check it too
                elif "adda247.com" in link and link not in visited_pages and "/jobs/" in link:
                    visited_pages.add(link)
                    try:
                        sub_res = requests.get(link, timeout=10)
                        sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                        for sub_link in sub_soup.find_all('a', href=True):
                            full_sub_link = urljoin(link, sub_link['href'])
                            if full_sub_link.endswith('.pdf'):
                                f_name = full_sub_link.split('/')[-1].split('?')[0]
                                f_path = os.path.join(folder_name, f_name)
                                if not os.path.exists(f_path):
                                    print(f"  Found in sub-page: {f_name}")
                                    r = requests.get(full_sub_link)
                                    with open(f_path, 'wb') as f:
                                        f.write(r.content)
                                    count += 1
                                    if count >= BATCH_SIZE: return
                    except:
                        continue
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    download_pdfs()
