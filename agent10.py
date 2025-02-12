import aiohttp
import asyncio
from seleniumwire import webdriver  # Selenium with network capture
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables for OpenAI API
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Asynchronous API Path Enumeration
async def async_api_check(url, paths):
    headers = {"User-Agent": "Mozilla/5.0"}
    graphql_query = {
        "query": "{ articles { title, body } }"
    }

    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(f"{url.rstrip('/')}{path}", json=graphql_query) if 'graphql' in path else session.get(f"{url.rstrip('/')}{path}") 
            for path in paths
        ]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            if response.status == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                print(f"API detected at {response.url}")
                return await response.json()
    return None


def run_async_api_check(url):
    paths = ["/api", "/v1", "/graphql", "/wp-json", "/data"]
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        return asyncio.ensure_future(async_api_check(url, paths))
    else:
        return asyncio.run(async_api_check(url, paths))


# Initialize Selenium Once
def start_selenium(url):
    options = Options()
    options.add_argument("--headless")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        return driver
    except Exception as e:
        print(f"Selenium initialization failed: {e}")
        return None


# Intercept API Calls (XHR/Fetch Monitoring)
def intercept_api_with_selenium(driver):
    api_endpoints = []
    time.sleep(5)  # Allow JavaScript to load
    for request in driver.requests:
        if '/api' in request.url or '/graphql' in request.url:
            api_endpoints.append(request.url)
            print(f"Intercepted API: {request.url}")
    return api_endpoints


# Fetch and Process the Most Relevant API
def fetch_and_process_relevant_api(api_endpoints):
    content_api = None
    relevant_keywords = ["content", "article", "body", "news", "title"]
    min_payload_size = 1000  # Minimum payload size to consider

    for endpoint in api_endpoints:
        try:
            response = requests.get(endpoint)
            if (
                response.status_code == 200 
                and 'application/json' in response.headers.get('Content-Type', '') 
                and len(response.content) > min_payload_size
            ):
                response_data = response.json()
                response_text = json.dumps(response_data)
                
                # Check for relevant keywords
                if any(keyword in response_text for keyword in relevant_keywords):
                    content_api = response_text
                    print(f"Processing intercepted API: {endpoint}")
                    process_web_content(response_text)
                    break
        except Exception as e:
            print(f"Failed to fetch {endpoint}: {e}")
    
    if not content_api:
        print("No suitable content API found. Summarizing fallback content.")


# Fallback to Dynamic Scraping (Reuse Selenium Browser)
def scrape_dynamic_with_existing_selenium(driver):
    try:
        time.sleep(3)  # Ensure full JavaScript load
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        return soup.get_text(), "Dynamic content successfully scraped with Selenium."
    except Exception as e:
        return "", f"Dynamic scrape failed: {e}"
    finally:
        driver.quit()  # Close Selenium after scraping


# Static Scraping with BeautifulSoup
def scrape_static(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(), "Static HTML successfully scraped."
    except Exception as e:
        return "", f"Static scrape failed: {e}"


# Concurrent Static and Dynamic Scraping
def scrape_static_and_dynamic(url, driver):
    with ThreadPoolExecutor() as executor:
        static_future = executor.submit(scrape_static, url)
        dynamic_future = executor.submit(scrape_dynamic_with_existing_selenium, driver)
        static_content, static_status = static_future.result()
        dynamic_content, dynamic_status = dynamic_future.result()

    print(static_status)
    print(dynamic_status)
    return static_content + "\n\n--- Dynamic Content ---\n\n" + dynamic_content


# Process and Summarize Web Content 
def process_web_content(content):
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

    # 1. Asynchronous API Check
    api_data = await run_async_api_check(url)

    if api_data:
        print("API data detected, processing...")
        process_web_content(json.dumps(api_data))  # Call process_web_content for API data
        return

    # 2. Start Selenium for XHR Monitoring
    print("No direct API found. Launching Selenium for XHR interception...")
    driver = start_selenium(url)
    if driver:
        intercepted_apis = intercept_api_with_selenium(driver)

        if intercepted_apis:
            print("Intercepted API endpoints:")
            for endpoint in intercepted_apis:
                print(endpoint)
            fetch_and_process_relevant_api(intercepted_apis)
            driver.quit()
            return

    # 3. Fallback to Scraping (Reuse Selenium)
    print("No API detected from XHR. Proceeding with scraping fallback...")
    content = scrape_static_and_dynamic(url, driver)
    process_web_content(content)  # Process scraped content with OpenAI


if __name__ == "__main__":
    target_url = "https://www.cnet.com/news/"
    asyncio.run(main(target_url))
