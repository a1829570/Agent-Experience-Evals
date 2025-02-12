from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import os
import json
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor


"""Use ThreadPoolExecutor to run bs4 and selenium concurrently, 
however, does not have the ability to evaluate whether the site contains js. 
If the site is purely static, selenium will run which is computationally expensive. 
Need a better method of discerning between site types. """
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Check for API endpoints first

def check_for_api(url):
    try:
        response = requests.get(url)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            print(f"Direct API detected at {url}!")
            return response.json()
    except requests.RequestException:
        pass

    api_paths = [
        "/api", "/v1", "/data", "/graphql", "/rest/v1",
        "/wp-json", "/api/v2", "/json", "/services", "/api/v3"
    ]

    for path in api_paths:
        api_test_url = f"{url.rstrip('/')}{path}"
        try:
            response = requests.get(api_test_url)
            if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                print(f"API detected at {api_test_url}!")
                return response.json()
        except requests.RequestException:
            continue

    print("No API endpoint found.")
    return None

# Static Scraping

def scrape_static(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        static_soup = BeautifulSoup(response.content, 'html.parser')
        return static_soup.get_text(), "Static HTML successfully scraped."
    except Exception as e:
        return "", f"Static scrape failed: {e}"

# Dynamic Scraping

def scrape_dynamic(url):
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        WebDriverWait(driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(10)
        page_source = driver.page_source
        driver.quit()
        dynamic_soup = BeautifulSoup(page_source, 'html.parser')
        return dynamic_soup.get_text(), "Dynamic JS content successfully scraped."
    except Exception as e:
        return "", f"Dynamic scrape failed: {e}"

# Concurrent Scraping

def scrape_static_and_dynamic(url):
    with ThreadPoolExecutor() as executor:
        static_future = executor.submit(scrape_static, url)
        dynamic_future = executor.submit(scrape_dynamic, url)
        static_content, static_status = static_future.result()
        dynamic_content, dynamic_status = dynamic_future.result()

    print(static_status)
    print(dynamic_status)
    combined_content = static_content + "\n\n--- Dynamic Content ---\n\n" + dynamic_content
    return combined_content

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

# Main Function

def main(url):
    print(f"Checking {url} for API endpoint...")
    api_data = check_for_api(url)

    if api_data:
        print("API data detected, processing...")
        process_web_content(json.dumps(api_data))
    else:
        print("No API found. Scraping static and dynamic content...")
        content = scrape_static_and_dynamic(url)
        process_web_content(content)

if __name__ == "__main__":
    target_url = "https://a1829570.github.io/web-scraping-test/index.html"  # Example URL
    main(target_url)
