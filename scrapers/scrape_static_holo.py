import logging
import time
import csv
import html
import re
import os
import pandas as pd
from sqlalchemy import create_engine, text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Note: This is meant to run as a standalone script & pushed to GitHub manually

############################################
# Configuration
############################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

BASE_URL = "https://hololive.hololivepro.com/en/talents"
DATA_PATH = "./data/talent_info.csv"
DB_URL = os.getenv("DB_URL")
ENGINE = create_engine(DB_URL)

############################################
# Utility Functions
############################################

# def setup_driver():
#     """
#     Windows ver
#     Sets up the Chrome WebDriver with headless mode.
#     """

#     options = Options()
#     options.add_argument("--headless")
    
#     return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def setup_driver():
    """
    Linux (Ubuntu) ver
    Sets up the Chrome WebDriver with headless mode.
    """
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium-browser"
    
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

def get_talent_urls(driver, url):
    """
    Loops through the main talents page and returns a list of talent URLs.
    Args:
        driver: WebDriver instance.
        url: The base URL to talents page.
    Returns:
        A list of unique talent URLs found on the page.
    """

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

def scrape_talent_info_static(driver, url):
    """
    Scrapes static information from each talent page, with built-in sleep time.
    Args:
        driver: WebDriver instance.
        url: The URL of the each single talent page.
    Returns:
        A single dictionary of talent information.
    """

    try:
        driver.get(url)

        # Wait for name to load, ideally would wait for other elements too
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".right_box .bg_box h1"))
        )

        # Extract name from the h1 element
        talent_name = driver.execute_script("""
            const h1 = document.querySelector('.right_box .bg_box h1');
            return h1?.childNodes[0]?.textContent.trim();
        """)

        # Extract information from the dd elements
        talent_info = driver.execute_script("""
            function scrape(labelText) {
                const normalize = str => str.trim().toLowerCase().replace(/\s+/g, "");
                const target = normalize(labelText);
                const dtList = Array.from(document.querySelectorAll("dt"));
                const dt = dtList.find(el => normalize(el.textContent) === target);
                return dt?.nextElementSibling?.textContent.trim() || null;
            }
            return {
                birthday: scrape("Birthday"),
                height: scrape("Height"),
                unit: scrape("Unit"),
                fan_name: scrape("Fan Name"),
                hashtags: scrape("Hashtags")
            };
        """)

        time.sleep(1.5) # Best practice
        return {
            "name": talent_name,
            **talent_info,
            "url": url
        }
    except Exception as e:
        logging.warning(f"Failed to extract info from {url}: {e}")
        return None

def data_preprocessing(data):
    """
    Preprocesses a list of dictionaries to save data as CSV.
    Args:
        data: List of dictionaries
    """
    try:
        if not data:
            logging.warning("No data found to save.")
            return

        # Clean data
        for item in data:
            for key, val in item.items():
                if isinstance(val, str):
                    item[key] = _clean_value(val)

        # Convert to df for further processing
        df = pd.DataFrame(data)
        
        # Supplement key column
        df_keys = pd.read_csv('./data/intermediate.csv')
        df = df.merge(df_keys, on='name', how='left')
        df = df[['Handle'] + [col for col in df.columns if col != 'Handle']]
        
        # Save directly as CSV
        df.to_csv(DATA_PATH, index=False, encoding="utf-8")
        logging.info("Preprocessing complete...")

    except Exception as e:
        logging.error(f"Preprocessing failed: {e}")

def _clean_value(value):
    """
    Internal utility function to clean and normalize string values.
    Otherwise it may cause issues when writing to CSV.
    Args:
        value: A single string value in a dictionary to clean.
    """

    # Handle missing values
    if not value:
        return "-"
    # Normalize newlines
    value = value.replace("\n", " | ").replace("\r", " ")
    # Normalize curly quotes to straight double/single quotes
    value = value.replace("“", '"').replace("”", '"')
    value = value.replace("‘", "'").replace("’", "'")
    # Unescape HTML entities
    value = html.unescape(value)
    # Replace double quotes with single quotes
    value = value.replace('"', "'")
    # Remove commas
    value = value.replace(",", "") 
    # Collapse multiple spaces
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip()

def data_loading():
    """
    Load CSV into database
    """
    df = pd.read_csv(DATA_PATH)

    with ENGINE.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS hololive"))

    df.to_sql("talent_info", ENGINE, schema="hololive", if_exists="replace", index=False)

def main():

    # Initialize the WebDriver and start the scraping process
    starttime = time.time()
    driver = setup_driver()

    # Get all talent URLs to start scraping
    try:
        all_urls = get_talent_urls(driver, BASE_URL)
        data_static_all = []
        for url in all_urls:
            data_static = scrape_talent_info_static(driver, url)
            if data_static:
                logging.info(f"Extracted {data_static}\n")
                data_static_all.append(data_static) # This is a list of dictionaries
        logging.info(f"Successfully extracted {len(data_static_all)} talents.")

        # Save the static data to CSV
        data_preprocessing(data_static_all)
        
        # Load data into DB
        data_loading()

    finally:
        driver.quit()
        endtime = time.time()
        runtime = endtime - starttime
        logging.info(f"Script completed in {runtime:.2f} seconds.")

if __name__ == "__main__":
    main()
