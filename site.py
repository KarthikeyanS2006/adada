import os
import re
import json
import time
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BATCH_SIZE = 50
DOWNLOAD_DIR = Path("pdfs")
BATCH_DIR = Path("batches")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

URLS = [
    "https://www.adda247.com/jobs/ssc-gd-previous-year-question-papers/",
    "https://www.adda247.com/jobs/ssc-chsl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cgl-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-mts-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-jht-previous-year-question-paper/",
    "https://www.adda247.com/jobs/ssc-cpo-previous-year-question-paper/",
]

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def get_page_with_selenium(url):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        html = driver.page_source
        driver.quit()
        return html
    except ImportError:
        print("Selenium not installed. Using basic requests...")
        return None
    except Exception as e:
        print(f"Selenium error: {e}")
        return None

def extract_pdf_links(html_content, base_url):
    pdf_links = []
    
    if not html_content:
        return pdf_links
    
    patterns = [
        r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
        r'data-url=["\']([^"\']*\.pdf[^"\']*)["\']',
        r'data-src=["\']([^"\']*\.pdf[^"\']*)["\']',
        r'"pdfUrl"\s*:\s*"([^"]+)"',
        r'"url"\s*:\s*"([^"]*\.pdf[^"]*)"',
        r'https?://[^"\']+\.pdf(?:\?[^"\']*)?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                full_url = urljoin(base_url, match)
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
    
    download_buttons = re.findall(
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(?:[^<]*Download[^<]*PDF[^<]*|<\/a>)',
        html_content, re.IGNORECASE
    )
    for btn in download_buttons:
        if btn.startswith('http'):
            if btn not in pdf_links:
                pdf_links.append(btn)
    
    return list(set(pdf_links))

def fetch_page(url):
    try:
        response = SESSION.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_pdf(url, dest_path, batch_num):
    try:
        response = SESSION.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.endswith('.pdf'):
            if response.content[:4] != b'%PDF':
                print(f"Skipping non-PDF: {url}")
                return False
        
        filename = dest_path.name
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"[Batch {batch_num}] Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def scrape_all_urls():
    all_pdfs = {}
    
    for url in URLS:
        print(f"\n{'='*60}")
        print(f"Scraping: {url}")
        print('='*60)
        
        html = fetch_page(url)
        
        if not html or 'adda247' in str(SESSION.headers.get('User-Agent', '')):
            html = get_page_with_selenium(url)
        
        if html:
            pdfs = extract_pdf_links(html, url)
            exam_name = re.search(r'ssc-(\w+)-previous', url)
            exam_key = exam_name.group(1) if exam_name else url.split('/')[-2]
            all_pdfs[exam_key] = pdfs
            print(f"Found {len(pdfs)} PDFs for {exam_key.upper()}")
        else:
            print(f"Failed to fetch page: {url}")
    
    return all_pdfs

def create_batches(pdf_list):
    batches = []
    for i in range(0, len(pdf_list), BATCH_SIZE):
        batch = pdf_list[i:i+BATCH_SIZE]
        batches.append(batch)
    return batches

def sanitize_filename(url):
    filename = url.split('/')[-1]
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    return filename[:100]

def save_batch_metadata(batches):
    metadata = {
        "created_at": datetime.now().isoformat(),
        "total_pdfs": sum(len(b) for b in batches),
        "batch_count": len(batches),
        "batches": []
    }
    
    for i, batch in enumerate(batches):
        batch_info = {
            "batch_number": i + 1,
            "count": len(batch),
            "pdfs": [{"url": url, "filename": sanitize_filename(url)} for url in batch]
        }
        metadata["batches"].append(batch_info)
    
    with open("batch_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Total PDFs: {metadata['total_pdfs']}, Batches: {len(batches)}")
    return metadata

def main():
    import shutil
    
    if BATCH_DIR.exists():
        shutil.rmtree(BATCH_DIR)
    BATCH_DIR.mkdir(exist_ok=True)
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    print("Starting SSC Papers Scraper...")
    print(f"Target: {len(URLS)} pages")
    print(f"Batch size: {BATCH_SIZE} PDFs")
    print()
    
    all_pdfs = scrape_all_urls()
    
    all_pdf_urls = []
    for exam, urls in all_pdfs.items():
        all_pdf_urls.extend(urls)
    
    all_pdf_urls = list(set(all_pdf_urls))
    
    print(f"\n{'='*60}")
    print(f"Total unique PDFs found: {len(all_pdf_urls)}")
    print('='*60)
    
    if all_pdf_urls:
        batches = create_batches(all_pdf_urls)
        metadata = save_batch_metadata(batches)
        
        print(f"\nCreated {len(batches)} batches")
        
        for i, batch in enumerate(batches):
            batch_num = i + 1
            batch_folder = BATCH_DIR / f"batch_{batch_num:02d}"
            batch_folder.mkdir(exist_ok=True)
            
            print(f"\n--- Processing Batch {batch_num:02d} ({len(batch)} PDFs) ---")
            
            for j, pdf_url in enumerate(batch):
                filename = sanitize_filename(pdf_url)
                dest = batch_folder / f"pdf_{j+1:03d}_{filename}"
                success = download_pdf(pdf_url, dest, batch_num)
                if success and dest.exists():
                    dest.rename(dest)
                time.sleep(1)
            
            print(f"Batch {batch_num:02d} complete: {len(list(batch_folder.glob('*.pdf')))} PDFs")
        
        print(f"\n{'='*60}")
        print("Scraping complete!")
        print(f"PDFs organized in {BATCH_DIR}/batch_XX/ folders")
        print('='*60)
        
        print("\n::set-output name=total_pdfs::" + str(metadata['total_pdfs']))
        print("::set-output name=batch_count::" + str(len(batches)))
    
    return all_pdfs

if __name__ == "__main__":
    main()
