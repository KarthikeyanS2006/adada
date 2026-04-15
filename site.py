import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Disable warnings for government/educational portals
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_SITES = {
    "Adda247_SSC": "https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/",
    "Adda247_Exams": "https://www.adda247.com/exams/upsc/upsc-previous-year-question-papers/"
}

BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 50 
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_organize_path(filename, folder):
    # Detect Year
    year = "Unknown_Year"
    match = re.search(r'20[0-2][0-9]', filename)
    if match: year = match.group(0)

    # Detect Exam Category
    fn = filename.upper()
    cat = "General"
    if "GD" in fn: cat = "SSC_GD"
    elif "CGL" in fn: cat = "SSC_CGL"
    elif "CHSL" in fn: cat = "SSC_CHSL"
    elif "TNPSC" in fn or "GROUP" in fn: cat = "TNPSC_Service"
    
    path = os.path.join(BASE_DIR, folder, year, cat)
    os.makedirs(path, exist_ok=True)
    return path

def run_scraper():
    session = requests.Session()
    session.headers.update(HEADERS)
    count = 0

    for folder, url in TARGET_SITES.items():
        if count >= BATCH_LIMIT: break
        print(f"\n--- Scraping {folder} ---")
        
        try:
            r = session.get(url, verify=False, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find all potential links
            all_a = soup.find_all('a', href=True)
            
            for a in all_a:
                if count >= BATCH_LIMIT: break
                link = urljoin(url, a['href'])
                
                # 1. Direct PDF Link
                if link.lower().endswith('.pdf'):
                    fname = link.split('/')[-1].split('?')[0]
                    target_dir = get_organize_path(fname, folder)
                    save_path = os.path.join(target_dir, fname)
                    
                    if not os.path.exists(save_path):
                        print(f"  Saving: {fname}")
                        pdf_data = session.get(link, verify=False).content
                        with open(save_path, 'wb') as f:
                            f.write(pdf_data)
                        count += 1
                
                # 2. Adda247 Sub-page (Look for Download pages)
                elif "adda247.com" in link and any(word in link for word in ["paper", "download", "pdf"]):
                    if link == url: continue # Skip if it's the same page
                    
                    try:
                        sr = session.get(link, verify=False, timeout=10)
                        ssoup = BeautifulSoup(sr.text, 'html.parser')
                        for sa in ssoup.find_all('a', href=True):
                            slink = urljoin(link, sa['href'])
                            if slink.lower().endswith('.pdf'):
                                sfname = slink.split('/')[-1].split('?')[0]
                                starget = get_organize_path(sfname, folder)
                                ssave = os.path.join(starget, sfname)
                                
                                if not os.path.exists(ssave):
                                    print(f"    Found in sub-page: {sfname}")
                                    spdf = session.get(slink, verify=False).content
                                    with open(ssave, 'wb') as f:
                                        f.write(spdf)
                                    count += 1
                                    if count >= BATCH_LIMIT: break
                    except:
                        continue
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_scraper()
