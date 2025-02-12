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


# 1) Import from formdetection.py
#    Make sure formdetection.py is in the same directory or PYTHONPATH
from formdetection import (
    fill_all_forms,  # main function that detects & fills forms
    start_selenium_with_wire,  # or you can keep agent’s own start_selenium_with_wire if you prefer
)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
two_captcha_key = os.getenv("TWO_CAPTCHA_API_KEY")
client = OpenAI(api_key=api_key)
def suppress_seleniumwire_logs_during_input():
    """
    Helper to temporarily suppress seleniumwire logs while user is typing.
    """
    sw_logger = logging.getLogger("seleniumwire")
    old_level = sw_logger.level
    sw_logger.setLevel(logging.CRITICAL)
    return old_level  # we’ll restore it manually
# ---------------------------
# Solve Turnstile with 2Captcha
# ---------------------------
def solve_turnstile(sitekey, page_url):
    """
    Attempt to solve Turnstile puzzle via 2Captcha,
    returning the token if successful, else None.
    """
    if not two_captcha_key:
        print("[ERROR] No 2Captcha key found.")
        return None

    solver = TwoCaptcha(two_captcha_key)
    try:
        # For older versions, use recaptcha(method='turnstile')
        result = solver.recaptcha(
            method='turnstile',
            sitekey=sitekey,
            url=page_url
        )
        token = result.get("code")
        if token:
            print(f"[INFO] 2Captcha Turnstile solve success: {token}")
            return token
        else:
            print("[ERROR] No 'code' in 2Captcha result.")
            return None
    except Exception as e:
        print(f"[ERROR] Turnstile solver exception: {e}")
        return None

def inject_turnstile_token(driver, token):
    """
    Inject the solved Turnstile token into the page,
    then refresh so Cloudflare can see it.
    """
    if not token:
        return
    try:
        driver.execute_script("""
          let tsField = document.querySelector('input[name="cf-turnstile-response"]');
          if (!tsField) {
              tsField = document.createElement('input');
              tsField.setAttribute('name','cf-turnstile-response');
              tsField.type = 'hidden';
              document.body.appendChild(tsField);
          }
          tsField.value = arguments[0];
        """, token)
        print("[INFO] Inserted Turnstile token. Refreshing page now.")
        driver.refresh()
        time.sleep(5)
    except Exception as e:
        print(f"[ERROR] Could not inject token: {e}")

# ---------------------------
# Start Selenium with "humanlike" moves
# ---------------------------
def start_selenium_with_wire(url):
    
    options = uc.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(
        service=service,
        seleniumwire_options={},
        options=options,
    )
    
    driver.get(url)
    # Simulate "humanlike" movements
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
      
     
    return driver

def check_direct_api(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            print(f"[INFO] Direct access success: {url}")
            return resp.json()
        else:
            print(f"API call failed with status code {resp.status_code}")
    except Exception as e:
        print(f"Direct API error: {e}")
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

# Intercept API Calls (XHR/Fetch Monitoring) with LLM Extraction
def intercept_api_with_selenium(driver):
    api_endpoints = []
    extracted_content = []
    sitekey = None
    domain = None

    time.sleep(5)  # Allow JavaScript to load
    for request in driver.requests:
        # Collect any interesting endpoints
        if any(api_key in request.url for api_key in ['/api', '/graphql', '/w/api.php']):
            api_endpoints.append(request.url)
            print(f"Intercepted API: {request.url}")

        # Check for Turnstile in requests
        if "turnstile" in request.url or "challenges.cloudflare.com" in request.url:
            #sitekey, domain = find_ephemeral_sitekey(driver)
            if sitekey:
                print(f"[INFO] Detected Turnstile sitekey: {sitekey}")
                break

    # Solve CAPTCHA if detected
    if sitekey:
        print("[INFO] Solving CAPTCHA...")
        token = solve_turnstile(sitekey, domain)
        if token:
            inject_turnstile_token(driver, token)
        else:
            print("[ERROR] Failed to solve CAPTCHA. Proceeding without solving.")

    # Use Crawl4AI for deeper content extraction
    if api_endpoints:
        strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=api_key,
            schema={"api_url": "string", "description": "string"},
            instruction="Extract API-like URLs and content from web responses and HTML bodies."
        )

        # Replace the old extract_from_urls call with a per-endpoint approach:
        for endpoint in api_endpoints:
            try:
                resp = requests.get(endpoint, timeout=10)
                if resp.status_code == 200:
                    # Use the doc's recommended method: extract_from_text
                    result = strategy.extract_from_text(resp.text)
                    if result:
                        extracted_content.append({
                            "endpoint": endpoint,
                            "parsed": result
                        })
            except Exception as e:
                print(f"[ERROR] Could not fetch {endpoint}: {e}")

        # Print or store the extracted data
        for content_item in extracted_content:
            print("Extracted using Crawl4AI:", content_item)

    # Pass intercepted API content to process_web_content if extracted
    if extracted_content:
        process_web_content(json.dumps(extracted_content))

    return api_endpoints


# Fallback scraping
def scrape_static_and_dynamic(url, driver):
    def scrape_static(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text(), "Static HTML successfully scraped."
        except Exception as e:
            return "", f"Static scrape failed: {e}"

    def scrape_dynamic(driver):
        try:
            time.sleep(3)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            return soup.get_text(), "Dynamic content successfully scraped with Selenium."
        except Exception as e:
            return "", f"Dynamic scrape failed: {e}"

    try:
        with ThreadPoolExecutor() as executor:
            static_future = executor.submit(scrape_static, url)
            dynamic_future = executor.submit(scrape_dynamic, driver)
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


# ---------------------------
# main() flow
# ---------------------------
async def main(url):
    print(f"Checking {url} for API endpoint...")
    # Direct API call
    api_data = check_direct_api(url)
    if api_data:
        process_web_content(json.dumps(api_data))
        return

    paths = ["/api/rest_v1/page/summary/API", "/api", "/v1", "/graphql", "/wp-json", "/data", "/w/api.php"]
    api_data = await async_api_check(url, paths)

    if api_data:
        print("API data detected, processing...")
        process_web_content(json.dumps(api_data))
        return

    print("No direct API found. Launching Selenium for XHR interception...")
    driver = start_selenium_with_wire(url)
    if driver:
        intercepted_apis = intercept_api_with_selenium(driver)

        if intercepted_apis:
            print("Intercepted API endpoints:")
            for endpoint in intercepted_apis:
                print(endpoint)
            # If you want to stop after intercepting APIs, you can return here.
            # Otherwise continue to fallback scraping below.
        else:
            print("No API detected from XHR. Proceeding with scraping fallback...")

        # >>>>>>> THIS is where we add form detection + user prompt <<<<<<
        # Show forms, let user decide to fill them:
        forms_exist = False
        # Let's check how many forms `fill_all_forms` sees (it logs itself).
        # But we only actually fill forms if user says yes.

        # We do a quick pass to see if forms exist:
        # (We could do the full fill_all_forms logic. We'll do a small tweak to let user choose.)
        from formdetection import gather_forms_from_dom
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

        # 4. If still no API, do fallback scraping
        content, _ = scrape_static_and_dynamic(url, driver)
        process_web_content(content)
    else:
        print("[ERROR] Could not launch driver.")


if __name__ == "__main__":
    target_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
    asyncio.run(main(target_url))
