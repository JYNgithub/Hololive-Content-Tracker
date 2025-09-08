import logging
import time
import html
import re
import os
import asyncio
import pandas as pd
from googletrans import Translator
from sqlalchemy import create_engine, text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Note: To scrape additional content, adjustments are made in scrape_talent_info_dynamic and _sort_columns 

############################################
# Configuration
############################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("googletrans").setLevel(logging.WARNING)

BASE_URL = "https://hololive.hololivepro.com/en/talents"
DATA_PATH = "./data/talent_schedule.csv"
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
    
def scrape_talent_info_dynamic(driver, url):
    """
    Scrapes dynamic information from each talent page, including name and schedules.
    Args:
        driver: WebDriver instance.
        url: The URL of each single talent page.
    Returns:
        A dictionary of talent information with schedule data.
    """

    try:
        driver.get(url)

        # Wait for the name to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".right_box .bg_box h1"))
        )

        # Extract name
        talent_name = driver.execute_script("""
            const h1 = document.querySelector('.right_box .bg_box h1');
            return h1?.childNodes[0]?.textContent.trim();
        """)

        # Extract default image
        main_image = driver.execute_script("""
            const img = document.querySelector('#talent_figure figure img');
            return img?.src || null;
        """)

        # Extract all schedule 
        schedule_data = driver.execute_script("""
            const slides = document.querySelectorAll('.talent_program .swiper-slide');
            if (!slides || slides.length === 0) return {};

            const result = {};
            Array.from(slides).forEach((slide, index) => {
                const i = index + 1;
                result["youtube_link" + i] = slide.querySelector("a")?.href || null;
                result["datetime" + i] = slide.querySelector(".cat")?.textContent.trim() || null;
                result["image" + i] = slide.querySelector("figure img")?.src || null;
                result["description" + i] = slide.querySelector(".txt_box .txt")?.textContent.trim() || null;
            });
            return result;
        """)

        time.sleep(1.5)
        return {
            "name": talent_name,
            "default_image": main_image,
            **schedule_data
        }

    except Exception as e:
        logging.warning(f"Failed to extract info from {url}: {e}")
        return None

async def data_preprocessing(data):
    """
    Preprocesses a list of dictionaries to save data as CSV with async translation.
    Note: Using googletrans==4.0.2 prevents dependency issues, but will need to handle async.
    Args:
        data: List of dictionaries
    """
    logging.info("Preprocessing data...")

    try:
        if not data:
            logging.error("No data to convert.")
            return pd.DataFrame()

        # Sort headers
        all_keys = set()
        for row in data:
            all_keys.update(row.keys())
        header = sorted(all_keys, key=_sort_columns)

        # Clean data
        cleaned_data = []
        for row in data:
            cleaned_row = {k: _clean_value(v) for k, v in row.items()}
            cleaned_data.append(cleaned_row)

        # Convert to df for further processing
        df = pd.DataFrame(cleaned_data, columns=header)

        # Async translate JP to EN
        translator = Translator()
        for col in df.columns:
            if col.lower().startswith("description"):
                for i, val in df[col].items():
                    df.at[i, col] = await translate_text(translator, val)
                    
        # Supplement key column            
        df_keys = pd.read_csv('./data/intermediate.csv')
        df = df.merge(df_keys, on='name', how='left')
        df = df[['Handle'] + [col for col in df.columns if col != 'Handle']]
        
        # Join data with talent_info
        df_info = pd.read_csv('./data/talent_info.csv')
        df = df.merge(df_info, on=["Handle", "name"], how="inner")
        
        # Sorting rows for sidebar appearance
        df_with_image = df[df['image1'].notna()]
        df_no_image = df[df['image1'].isna()]
        df = pd.concat([df_with_image, df_no_image])
        mask_bracket = df['name'].str.contains(r'\[.*\]', na=False)
        df = pd.concat([df[~mask_bracket], df[mask_bracket]])
        df = df.reset_index(drop=True)
        df.index += 1

        # Save directly as CSV
        df.to_csv(DATA_PATH, index=False, encoding="utf-8")
        logging.info("Preprocessing complete...")

    except Exception as e:
        logging.error(f"Preprocessing failed: {e}")

async def translate_text(translator, text):
    if pd.isna(text):
        return text
    try:
        result = await translator.translate(str(text), src='ja', dest='en')
        return result.text
    except:
        return text

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

def _sort_columns(key):
    """
    Internal utility function to sort column names in a specific order.
    Used in save_to_csv_dynamic at line 'header = sorted(all_keys, key=_sort_columns)'.
    """

    col_order = ["name", "default_image", "datetime", "description", "image", "youtube_link"]
    for i, prefix in enumerate(col_order):
        if key.startswith(prefix):
            m = re.match(rf"{prefix}(\d*)$", key)
            suffix = int(m.group(1)) if m and m.group(1).isdigit() else 0
            return (i, suffix) # Unmatched keys go at the end
        
    return (len(col_order), key)

def data_loading():
    """
    Load CSV into database
    """
    df = pd.read_csv(DATA_PATH)

    df.to_sql("talent_schedule", ENGINE, schema="hololive", if_exists="replace", index=False)

def main():

    # Initialize the WebDriver and start the scraping process
    starttime = time.time()
    driver = setup_driver()

    # Get all talent URLs to start scraping
    try:
        all_urls = get_talent_urls(driver, BASE_URL)
        data_dynamic_all = []
        for url in all_urls:
            data_dynamic = scrape_talent_info_dynamic(driver, url)
            if data_dynamic:
                logging.info(f"Extracted {data_dynamic}\n")
                data_dynamic_all.append(data_dynamic) # This is a list of dictionaries
        logging.info(f"Successfully extracted {len(data_dynamic_all)} talents.")

        # Preprocess data to save as csv
        asyncio.run(data_preprocessing(data_dynamic_all))
        
        # Load data into DB
        data_loading()

    finally:
        driver.quit()
        endtime = time.time()
        runtime = endtime - starttime
        logging.info(f"Script completed in {runtime:.2f} seconds.")

if __name__ == "__main__":
    main()
