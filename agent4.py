"""Check for API Endpoints First – Directly fetch data in JSON format if the site offers an API.
Dynamic Scraping (Selenium) – Handle JavaScript-heavy websites if no API is found.
Static Scraping (BeautifulSoup) – Fallback to simple HTML scraping if Selenium fails.
Assistant API for Processing – Use OpenAI’s Assistants API to analyze, summarize, and extract insights from the data."""


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import re
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initializes the OpenAI client by passing an API key.
#This allows the program to interact with the OpenAI Assistants API for text summarization and content analysis.
client = OpenAI(api_key=api_key)

def check_for_api(url):
    # Check if the URL itself might be an API endpoint
    try:
        response = requests.get(url)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            print(f"Direct API detected at {url}!")
            return response.json()
    except requests.RequestException:
        pass

    # Standard API paths to check
    api_paths = [
        "/api", "/v1", "/data", "/graphql", "/rest/v1",
        "/wp-json", "/api/v2", "/json", "/services", "/api/v3"
    ]

    # Append common API paths to the URL and test them
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


def scrape_with_selenium(url):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    # Extract full HTML
    page_source = driver.page_source
    driver.quit()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    
    content = soup
    
    # Extract and return the article text
    return soup.get_text() if content else "No main content found."



def scrape_with_bs4(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()


def process_web_content(content):
    # Create Assistant with Code Interpreter
    assistant = client.beta.assistants.create(
        name="Web Content Summarizer",
        instructions="You are an assistant that extracts and summarizes web data using Python.",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4-turbo"
    )

    # Create Thread
    thread = client.beta.threads.create()

    # Add Content to Assistant
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Extract the following content and give it back word for word:\n\n{content[:3000]}"
    )

    # Execute Task
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Extract the following content and give it back word for word."
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == "assistant":
                print(message.content[0].text.value)
    else:
        print(f"Run status: {run.status}")


def main(url):
    print(f"Checking {url} for API endpoint...")
    api_data = check_for_api(url)

    if api_data:
        print("API data detected, processing...")
        process_web_content(json.dumps(api_data))
    else:
        print("No API found. Attempting web scraping...")
        try:
            content = scrape_with_selenium(url)
            print("Dynamic content scraped with Selenium.")
        except Exception as e:
            print(f"Selenium scrape failed: {e}. Using BeautifulSoup...")
            content = scrape_with_bs4(url)

        process_web_content(content)


if __name__ == "__main__":
    target_url = "https://a1829570.github.io/web-scraping-test/dynamic.html" # Replace with target website
    main(target_url)
