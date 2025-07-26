import logging
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

############################################
# Configuration
############################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

base_url = "https://hololive.hololivepro.com/en/talents"

############################################
# Utility Functions
############################################

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_talent_urls(driver, url):
    logging.info(f"Loading base page: {url}")
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/talents/"]'))
        )
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/talents/"]')
        urls = set()

        for el in elements:
            href = el.get_attribute('href')
            if href and href.startswith(url):
                urls.add(href)

        logging.info(f"Found {len(urls)} talent urls")
        return list(urls)

    except Exception as e:
        logging.error(f"Error fetching talent urls: {e}")
        return []
    
def scrape_talent_info_dynamic(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".talent_program_list"))
        )
        programs = driver.execute_script("""
            const results = [];
            document.querySelectorAll('.talent_program_list li a').forEach(el => {
                const href = el.href;
                const txt = el.querySelector('p.txt')?.textContent.trim();
                const catEl = el.querySelector('p.cat, p.cat.now_on_air');
                const cat = catEl ? catEl.textContent.trim() : null;
                if (href && txt) {
                    results.push({ href, txt, cat });
                }
            });
            return results;
        """)
        logging.info(f"Extracted {len(programs)} program(s)")
        time.sleep(1.5)
        return programs

    except Exception as e:
        logging.warning(f"Failed to extract programs from {url}: {e}")
        return []
    
def save_to_csv_dynamic(data, filename):
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title", "Link", "Category"])  
        for item in data:
            writer.writerow([item['txt'], item['href'], item['cat']])
    logging.info(f"Results saved to {filename}")

def main():
    starttime = time.time()
    driver = setup_driver()
    try:
        all_urls = get_talent_urls(driver, base_url)
        data_dynamic_all = []
        for url in all_urls:
            data_dynamic = scrape_talent_info_dynamic(driver, url)
            if data_dynamic:
                for item in data_dynamic:
                    data_dynamic_all.append((item['txt'], item['href'], item['cat']))
        logging.info(f"Successfully extracted {len(data_dynamic_all)} programs.")
        save_to_csv_dynamic(data_dynamic_all, "talent_schedule.csv")
    finally:
        driver.quit()
        endtime = time.time()
        runtime = endtime - starttime
        logging.info(f"Script completed in {runtime:.2f} seconds.")

if __name__ == "__main__":
    main()
