import requests
from playwright.sync_api import sync_playwright
import time, random

URL = "https://hololive-content-tracker.onrender.com"

# Check if site is alive
try:
    r = requests.get(URL, timeout=10)
    print(f"Site alive: Code {r.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Site unreachable: {e}")
    exit()

# Simulate user activity
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    agent = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )
    page = agent.new_page()

    # Navigate to the site and wait for it to load
    page.goto(URL)
    # page.wait_for_load_state("networkidle")
    page.wait_for_load_state("domcontentloaded")

    # # Unused for now
    # # Action to mimic human behaviour
    # for _ in range(5):
    #     page.evaluate(f"window.scrollBy(0, {random.randint(300, 600)})")
    #     time.sleep(random.uniform(0.5, 1.5))

    time.sleep(5)
    print("Done keep awake for ", page.title())
    browser.close()