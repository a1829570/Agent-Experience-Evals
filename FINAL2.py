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
from form_handling.formdetection import (
    fill_all_forms,  # main function that detects & fills forms
)
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
solver = TwoCaptcha(CAPTCHA_API_KEY)


# Set human-like User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
def suppress_seleniumwire_logs_during_input():
    """
    Helper to temporarily suppress seleniumwire logs while user is typing.
    """
    sw_logger = logging.getLogger("seleniumwire")
    old_level = sw_logger.level
    sw_logger.setLevel(logging.CRITICAL)
    return old_level  # we’ll restore it manually

from undetected_chromedriver import Chrome, ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import platform
import subprocess

def get_local_chrome_version():
    system = platform.system()
    if system == "Windows":
        import winreg
        reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, reg_path)
            version, _ = winreg.QueryValueEx(key, "version")
            return version
        except Exception:
            return None
    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                capture_output=True, text=True
            )
            return result.stdout.strip().split()[-1]
        except Exception:
            return None
    else:
        try:
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            return result.stdout.strip().split()[-1]
        except Exception:
            return None

def configure_driver():
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-webrtc")
    options.add_argument(f"user-agent={USER_AGENT}")

    driver_path = ChromeDriverManager().install()
    print(f"[INFO] Using ChromeDriver: {driver_path}")

    chrome_version = get_local_chrome_version()
    if not chrome_version:
        raise RuntimeError("Could not detect Chrome version.")
    
    version_main = int(chrome_version.split('.')[0])
    driver = Chrome(driver_executable_path=driver_path, options=options, version_main=version_main)
    return driver


"""def intercept_xhr_requests(driver):
    #Intercept API calls (XHRs) using Chrome DevTools Protocol (CDP) and apply LLM extraction.
    print("[INFO] Enabling XHR interception using CDP...")

    intercepted_apis = []
    extracted_content = []
    
    def on_request_sent(request):
        url = request['request']['url']
        headers = request['request']['headers']
        if any(api_keyword in url for api_keyword in ["/api", "/graphql", "/w/api.php"]):
            print(f"[INFO] Intercepted API: {url}")
            print(f"[INFO] Captured Headers: {headers}")
            intercepted_apis.append({"url": url, "headers": headers})

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setRequestInterception", {"patterns": [{"urlPattern": "*"}]})
    driver.add_cdp_listener("Network.requestWillBeSent", on_request_sent)

    # Apply LLM extraction to intercepted API endpoints
    if intercepted_apis:
        strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=api_key,
            schema={"api_url": "string", "description": "string"},
            instruction="Extract API-like URLs and content from web responses and HTML bodies."
        )

        for api in intercepted_apis:
            try:
                resp = requests.get(api['url'], headers=api['headers'], timeout=10)
                if resp.status_code == 200:
                    result = strategy.extract_from_text(resp.text)
                    if result:
                        extracted_content.append({"endpoint": api['url'], "parsed": result})
            except Exception as e:
                print(f"[ERROR] Could not fetch {api['url']}: {e}")

        # Print extracted API data
        for content_item in extracted_content:
            print("[INFO] Extracted using Crawl4AI:", content_item)

    return extracted_content
"""
def start_browser(url):
    """Launches the browser, attempts to bypass CAPTCHA, and proceeds with scraping."""
    print(f"[INFO] Launching browser to access: {url}")
    driver = configure_driver()
    driver.get(url)
    time.sleep(5)  # Wait for page to load
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]
    actions = ActionChains(driver)
    for _ in range(random.randint(3, 7)):
        x_offset = random.randint(-width // 2, width // 2)
        y_offset = random.randint(-height // 2, height // 2)
        try:
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.5, 1.2))
        except MoveTargetOutOfBoundsException:
            pass
    """
    extracted_apis = intercept_xhr_requests(driver)

    if extracted_apis:
        process_web_content(json.dumps(extracted_apis))
    """

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

import re  # Add to your imports if not already present

def process_web_content(content):
    print("Processing Web Content...")

    # Clean and truncate content
    cleaned = re.sub(r'\s+', ' ', content)
    content_to_send = cleaned[:3000]

    # Create assistant
    assistant = client.beta.assistants.create(
        name="Web Extractor",
        instructions="You are a helpful assistant that extracts structured key points such as names, dates, locations, and facts from HTML web content. Focus on clarity and brevity.",
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}]
    )

    # Create thread and send message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Extract and summarize key facts from this page content:\n\n{content_to_send}"
    )

    # Start run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Focus on summarizing the most important content from the user's message."
    )

    # Poll run status
    while True:
        current_run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if current_run.status == "completed":
            break
        elif current_run.status in ["failed", "cancelled", "expired"]:
            print(f"Run status: {current_run.status}")
            if current_run.last_error:
                print("Error details:", current_run.last_error)
            return
        time.sleep(2)

    # Get assistant message response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == "assistant":
            print(message.content[0].text.value)

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

# Asynchronous API Path Enumeration with Crawl4AI Integration
async def async_api_check(url, paths):
    headers = {"User-Agent": "Mozilla/5.0"}
    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=api_key,
        schema={"api_url": "string", "description": "string"},
        instruction="Extract API endpoints or references from web content or JSON data."
    )

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(f"{url.rstrip('/')}{path}", headers=headers) for path in paths
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                print(f"Request failed: {response}")
                continue
            if response.status == 200:
                print(f"Potential API response at {response.url}")
                extracted_content = extraction_strategy.extract_from_text(await response.text())
                if extracted_content:
                    print("Extracted API content with LLM:", extracted_content)
                    return extracted_content
    return None


async def main(url):
    print(f"[INFO] Checking {url} for API access...")
    
    # Step 1: Attempt Direct API Call
    api_data = await check_direct_api(url)
    if api_data:
        print("[INFO] API data detected, skipping scraping.")
        return api_data

    paths = ["/api/rest_v1/page/summary/API", "/api", "/v1", "/graphql", "/wp-json", "/data", "/w/api.php"]
    api_data = await async_api_check(url, paths)

    if api_data:
        print("API data detected, processing...")
        process_web_content(json.dumps(api_data))
        return

    # Step 2: Launch Browser
    print("[INFO] No API found, launching browser for scraping...")
    driver = start_browser(url)
    if driver:
        forms_exist = False
        # Let's check how many forms `fill_all_forms` sees (it logs itself).
        # But we only actually fill forms if user says yes.

        # We do a quick pass to see if forms exist:
        # (We could do the full fill_all_forms logic. We'll do a small tweak to let user choose.)
        from form_handling.formdetection import gather_forms_from_dom
        forms = gather_forms_from_dom(driver)
        if forms:
            forms_exist = True
            print(f"[INFO] {len(forms)} form(s) detected on the page.")

        if forms_exist:
            choice = input("Form(s) found. Do you want to fill them? (y/n): ").strip().lower()
            if choice == 'y':
                old_level = suppress_seleniumwire_logs_during_input()
                try:
                    fill_all_forms(driver)  # This calls user input for each field
                finally:
                    logging.getLogger("seleniumwire").setLevel(old_level)
            else:
                print("Skipping form-filling step.")
        # Step 3: Scrape Page Content
        content, _ = scrape_page(driver)
        process_web_content(content)

if __name__ == "__main__":
    target_url = "https://en.wikipedia.org/wiki/Cristiano_Ronaldo"
    asyncio.run(main(target_url))
