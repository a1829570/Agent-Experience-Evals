import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha
import requests
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import SeleniumWire only when needed (prevents CAPTCHA detection)
try:
    from seleniumwire import webdriver  # API interception only when necessary
    SELENIUMWIRE_AVAILABLE = True
except ImportError:
    SELENIUMWIRE_AVAILABLE = False

# Load environment variables
load_dotenv()
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
solver = TwoCaptcha(CAPTCHA_API_KEY)

# Set a human-like User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

def configure_driver(use_seleniumwire=False, use_cookies=None):
    """Configures ChromeDriver with optional SeleniumWire and session persistence."""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_argument("--disable-webrtc")  # Prevent WebRTC leaks

    # Use undetected_chromedriver first
    if use_seleniumwire and SELENIUMWIRE_AVAILABLE:
        driver = webdriver.Chrome(options=options, seleniumwire_options={})
    else:
        driver = uc.Chrome(options=options)

    # Restore session cookies (if available)
    if use_cookies:
        driver.get("https://platform.openai.com")  # Load the base domain first
        for cookie in use_cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        print("[INFO] Restored previous session cookies.")

    return driver

def detect_captcha(driver):
    """Checks if CAPTCHA is present on the page."""
    print("[INFO] Checking for CAPTCHA...")
    captcha_elements = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
    return len(captcha_elements) > 0

def solve_captcha(driver, page_url):
    """Solves Cloudflare CAPTCHA if detected."""
    try:
        print("[INFO] Detecting CAPTCHA on the page...")
        captcha_elements = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
        if not captcha_elements:
            print("[INFO] No CAPTCHA detected.")
            return True  # No CAPTCHA to solve

        print(f"[INFO] Found {len(captcha_elements)} CAPTCHA(s). Solving...")

        # Extract sitekey
        sitekey = driver.execute_script("""
            let captchaFrame = document.querySelector("iframe[src*='captcha']");
            if (captchaFrame) {
                let src = captchaFrame.getAttribute("src");
                let match = src.match(/k=([a-zA-Z0-9_-]+)/);
                return match ? match[1] : null;
            }
            return null;
        """)

        if not sitekey:
            print("[ERROR] No sitekey found for CAPTCHA.")
            return False

        # Solve CAPTCHA using 2Captcha API
        result = solver.recaptcha(sitekey=sitekey, url=page_url)
        if "code" in result:
            solved_token = result["code"]
            print("[INFO] CAPTCHA solved successfully.")

            # Inject token
            driver.execute_script(f"""
                let captchaInput = document.querySelector("textarea[name='cf-turnstile-response']");
                if (!captchaInput) {{
                    captchaInput = document.createElement('textarea');
                    captchaInput.setAttribute('name', 'cf-turnstile-response');
                    captchaInput.style.display = 'none';
                    document.body.appendChild(captchaInput);
                }}
                captchaInput.value = arguments[0];
            """, solved_token)

            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
            time.sleep(5)  # Allow site processing
            print("[SUCCESS] CAPTCHA bypassed!")
            return True

        print("[ERROR] CAPTCHA solving failed.")
        return False

    except Exception as e:
        print(f"[ERROR] CAPTCHA solving error: {e}")
        return False

def scrape_with_api_interception(url, cookies):
    """Starts SeleniumWire session for API interception (only if no CAPTCHA was found)."""
    print("[INFO] Launching browser for API interception...")
    driver = configure_driver(use_seleniumwire=True, use_cookies=cookies)
    driver.get(url)
    time.sleep(5)  # Allow page to load

    # Extract API calls
    api_endpoints = []
    try:
        for request in driver.requests:
            if any(api_path in request.url for api_path in ["/api", "/graphql", "/w/api.php"]):
                api_endpoints.append(request.url)
                print(f"[INFO] Intercepted API: {request.url}")
    except Exception as e:
        print(f"[ERROR] API interception failed: {e}")

    driver.quit()
    return api_endpoints

def start_scraping(url):
    """Handles page loading, CAPTCHA detection, and optional API interception."""
    print(f"[INFO] Accessing {url}...")
    driver = configure_driver()
    driver.get(url)
    time.sleep(5)  # Allow page to load

    # Step 1: Store session cookies (to persist login state)
    cookies = driver.get_cookies()

    # Step 2: Check for CAPTCHA
    if detect_captcha(driver):
        print("[WARNING] CAPTCHA detected. Solving...")
        if not solve_captcha(driver, url):
            print("[ERROR] CAPTCHA could not be solved. Exiting...")
            driver.quit()
            return

    # Step 3: If no CAPTCHA, intercept APIs using stored session cookies
    if SELENIUMWIRE_AVAILABLE:
        print("[INFO] Restarting with API interception enabled...")
        api_endpoints = scrape_with_api_interception(url, cookies)
        print("[INFO] Intercepted API Endpoints:", api_endpoints)
    else:
        print("[INFO] SeleniumWire not installed. Skipping API interception.")

    driver.quit()
    print("[INFO] Scraping completed.")

# Run the script
if __name__ == "__main__":
    target_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
    start_scraping(target_url)
