import aiohttp
import asyncio
from seleniumwire import webdriver  # Selenium with network capture
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from undetected_chromedriver import Chrome, ChromeOptions  # Use undetected_chromedriver for bypassing detection
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


# Load environment variables for OpenAI API
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Initialize Selenium for Dynamic Scraping
def start_selenium_with_wire(url):
    options = uc.ChromeOptions()
    options.add_argument("--headless")  # Optional: Remove for debugging
    options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation features
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")

    # Create a service object for the ChromeDriver
    service = Service(ChromeDriverManager().install())

    # Integrate selenium-wire with undetected-chromedriver
    driver = webdriver.Chrome(
        service=service,  # Pass the service object here
        seleniumwire_options={},  # Enables request interception
        options=options,
    )

    # Navigate to the page
    driver.get(url)


    # Simulate human behavior
    window_size = driver.get_window_size()
    width, height = window_size["width"], window_size["height"]

    actions = ActionChains(driver)
    for _ in range(random.randint(5, 10)):
        x_offset = random.randint(-width // 2, width // 2)
        y_offset = random.randint(-height // 2, height // 2)
        try:
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.5, 1.5))
        except MoveTargetOutOfBoundsException:
            pass

    # Additional human-like interactions
    try:
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(random.uniform(0.5, 1.5))
        driver.execute_script("window.scrollBy(0, -150);")
        time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:
        print(f"Error during scrolling simulation: {e}")

    return driver


# Check Direct API Access
def check_direct_api(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"Direct API access successful: {url}")
            return response.json()
        else:
            print(f"API call failed with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Direct API call error: {e}")
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
    time.sleep(5)  # Allow JavaScript to load
    for request in driver.requests:
        if any(api_key in request.url for api_key in ['/api', '/graphql', '/w/api.php']):
            api_endpoints.append(request.url)
            print(f"Intercepted API: {request.url}")

    return api_endpoints

# Fallback: Static and Dynamic Scraping
def scrape_static_and_dynamic(url, driver):
    def scrape_static(url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
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
#Process and Summarize Web Content 
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
# Main Workflow (API Detection, XHR Interception, Scraping Fallback)
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
                process_web_content(endpoint)  # Pass each intercepted API to process_web_content
            driver.quit()
            return

    print("No APIs detected. Proceeding with scraping fallback...")
    content, _ = scrape_static_and_dynamic(url, driver)
    process_web_content(content)

if __name__ == "__main__":
    target_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
    asyncio.run(main(target_url))
