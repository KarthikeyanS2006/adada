import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Silence SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_SITES = {
    "Adda247": "https://www.adda247.com/exams/upsc/upsc-previous-year-question-papers/",
    "Adda247_SSC": "https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/"
}

BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 50
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def organize_file(filename, source_folder):
    year_match = re.search(r'20[0-2][0-9]', filename)
    year = year_match.group(0) if year_match else "Unknown_Year"
    
    exam_type = "General"
    fn_upper = filename.upper()
    if any(x in fn_upper for x in ["G4", "GROUP_IV", "GROUP-IV", "GD"]): exam_type = "Group_GD_4"
    elif any(x in fn_upper for x in ["G2", "GROUP_II", "GROUP-II", "CGL"]): exam_type = "Group_CGL_2"
    elif "PRELIM" in fn_upper: exam_type = "Prelims"
    elif "MAIN" in fn_upper: exam_type = "Mains"

    target_path = os.path.join(BASE_DIR, source_folder, year, exam_type)
    os.makedirs(target_path, exist_ok=True)
    return target_path

def download_file(url, target_dir):
    try:
        original_name = url.split('/')[-1].split('?')[0]
        final_path = os.path.join(target_dir, original_name)
        
        if not os.path.exists(final_path):
            print(f"    Downloading: {original_name}")
            r = requests.get(url, stream=True, verify=False, timeout=20, headers=HEADERS)
            with open(final_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def scrape():
    new_files_count = 0
    visited_links = set()

    for folder_name, start_url in TARGET_SITES.items():
        if new_files_count >= BATCH_LIMIT: break
        print(f"\n--- Processing {folder_name} ---")
        
        try:
            res = requests.get(start_url, headers=HEADERS, verify=False, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Find all links on the main page
            for a in soup.find_all('a', href=True):
                if new_files_count >= BATCH_LIMIT: break
                
                link = urljoin(start_url, a['href'])
                
                # Check if it's a PDF
                if link.lower().endswith('.pdf'):
                    target_dir = organize_file(link.split('/')[-1], folder_name)
                    if download_file(link, target_dir):
                        new_files_count += 1
                
                # Deep Crawl: If it's an Adda247 article link, go inside it
                elif "adda247.com/jobs/" in link and link not in visited_links:
                    visited_links.add(link)
                    print(f"  Checking sub-page: {link}")
                    try:
                        sub_res = requests.get(link, headers=HEADERS, verify=False, timeout=10)
                        sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                        for sub_a in sub_soup.find_all('a', href=True):
                            sub_link = urljoin(link, sub_a['href'])
                            if sub_link.lower().endswith('.pdf'):
                                target_dir = organize_file(sub_link.split('/')[-1], folder_name)
                                if download_file(sub_link, target_dir):
                                    new_files_count += 1
                                    if new_files_count >= BATCH_LIMIT: break
                    except:
                        continue
        except Exception as e:
            print(f"Error connecting to {folder_name}: {e}")

if __name__ == "__main__":
    scrape()
