import aiohttp
import asyncio
from seleniumwire import webdriver  # For network intercept
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
import random
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import os
from dotenv import load_dotenv
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from selenium.common.exceptions import MoveTargetOutOfBoundsException
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
import asyncio
import logging
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
solver = TwoCaptcha(CAPTCHA_API_KEY)

# Set human-like User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

def configure_driver():
    """Configures an undetected ChromeDriver with stealth settings."""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_argument("--disable-webrtc")  # Prevent WebRTC leaks

    chrome_executable_path = ChromeDriverManager().install()
    print(f"[INFO] Using ChromeDriver: {chrome_executable_path}")

    driver = uc.Chrome(driver_executable_path=chrome_executable_path, options=options)
    return driver

def solve_captcha(driver, page_url):
    """Detects and solves Cloudflare Turnstile CAPTCHA."""
    try:
        print("[INFO] Detecting CAPTCHA on the page...")
        captcha_elements = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
        if captcha_elements:
            print(f"[INFO] Found {len(captcha_elements)} CAPTCHA(s) on the page.")

            sitekey = driver.execute_script("""
                let captchaFrame = document.querySelector("iframe[src*='captcha']");
                if (captchaFrame) {
                    let src = captchaFrame.getAttribute("src");
                    let match = src.match(/k=([a-zA-Z0-9_-]+)/);
                    return match ? match[1] : null;
                }
                return null;
            """)

            if sitekey:
                print(f"[INFO] CAPTCHA sitekey detected: {sitekey}")

                # Solve CAPTCHA using 2Captcha API
                print("[INFO] Sending CAPTCHA for solving...")
                result = solver.recaptcha(sitekey=sitekey, url=page_url)

                if 'code' in result:
                    solved_token = result["code"]
                    print(f"[INFO] CAPTCHA solved successfully: {solved_token}")

                    # Inject the token into the correct field
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

                    print("[INFO] Injected CAPTCHA token into the page.")

                    # Submit the CAPTCHA response
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
                    time.sleep(5)  # Allow site to process token
                    print("[SUCCESS] CAPTCHA bypassed!")

                    return True
                else:
                    print("[ERROR] Failed to solve CAPTCHA.")
                    return False
            else:
                print("[ERROR] No sitekey found on the page.")
                return False
        else:
            print("[INFO] No CAPTCHA detected on this page.")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during CAPTCHA solving: {e}")
        return False

def start_browser(url):
    """Launches the browser, attempts to bypass CAPTCHA, and proceeds with scraping."""
    print(f"[INFO] Launching browser to access: {url}")
    driver = configure_driver()
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    # Solve CAPTCHA if present
    if solve_captcha(driver, url):
        print("[INFO] Continuing normal browsing...")
    else:
        print("[INFO] No CAPTCHA detected or solving failed.")

    return driver

def scrape_page(driver):
    """Extracts page content dynamically and statically."""
    def scrape_static():
        try:
            response = requests.get(driver.current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text(), "Static HTML successfully scraped."
        except Exception as e:
            return "", f"Static scrape failed: {e}"

    def scrape_dynamic():
        try:
            time.sleep(3)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            return soup.get_text(), "Dynamic content successfully scraped with Selenium."
        except Exception as e:
            return "", f"Dynamic scrape failed: {e}"

    try:
        with ThreadPoolExecutor() as executor:
            static_future = executor.submit(scrape_static)
            dynamic_future = executor.submit(scrape_dynamic)
            static_content, static_status = static_future.result()
            dynamic_content, dynamic_status = dynamic_future.result()
    finally:
        driver.quit()  # Ensure the driver quits to free resources

    print(static_status)
    print(dynamic_status)

    combined_content = static_content + "\n\n--- Dynamic Content ---\n\n" + dynamic_content
    return combined_content, static_status + "; " + dynamic_status

def process_web_content(content):
    print("Processing Web Content...")
    assistant = client.beta.assistants.create(
        name="Web Content Summarizer",
        instructions="You are an assistant that extracts and summarizes web data using Python.",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4-turbo"
    )

    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Extract and summarize the following content:\n\n{content[:3000]}"
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Extract key information from the provided content."
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == "assistant":
                print(message.content[0].text.value)
    else:
        print(f"Run status: {run.status}")



async def check_direct_api(url):
    """Checks for direct API access before attempting scraping."""
    try:
        headers = {"User-Agent": USER_AGENT}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    print(f"[INFO] Direct API success: {url}")
                    return await resp.json()
                else:
                    print(f"[ERROR] API call failed with status code {resp.status}")
    except Exception as e:
        print(f"[ERROR] Direct API error: {e}")
    return None

async def main(url):
    print(f"[INFO] Checking {url} for API access...")
    
    # Step 1: Attempt Direct API Call
    api_data = await check_direct_api(url)
    if api_data:
        print("[INFO] API data detected, skipping scraping.")
        return api_data

    # Step 2: Launch Browser
    print("[INFO] No API found, launching browser for scraping...")
    driver = start_browser(url)
    if driver:
        # Step 3: Scrape Page Content
        content, _ = scrape_page(driver)
        process_web_content(content)

if __name__ == "__main__":
    target_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
    asyncio.run(main(target_url))
