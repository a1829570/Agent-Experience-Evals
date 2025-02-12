import aiohttp
import asyncio
from seleniumwire import webdriver  # Selenium with network capture
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from undetected_chromedriver import Chrome, ChromeOptions
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager
import random
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Rotating Proxies and User-Agent
proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]

def get_random_proxy():
    return random.choice(proxies)

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

# Improved Selenium Initialization
def start_selenium(url):
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    # Uncomment below for visible browser (better evasion)
    # options.add_argument("--headless")
    proxy = get_random_proxy()

    seleniumwire_options = {
        "proxy": {
            "http": proxy,
            "https": proxy,
        }
    }

    driver = Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
        seleniumwire_options=seleniumwire_options,
    )
    driver.get(url)

    # Simulate human-like behavior
    actions = ActionChains(driver)
    try:
        for _ in range(random.randint(5, 10)):
            x_offset = random.randint(-200, 200)
            y_offset = random.randint(-200, 200)
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.2, 1.5))
    except Exception as e:
        print(f"Human-like behavior simulation failed: {e}")

    return driver

# Direct API Check
def check_direct_api(url):
    headers = {"User-Agent": get_random_user_agent()}
    try:
        response = requests.get(
            url,
            headers=headers,
            proxies={"http": get_random_proxy(), "https": get_random_proxy()},
        )
        if response.status_code == 200:
            print("Direct API access successful!")
            return response.text
        else:
            print(f"API call failed with status code {response.status_code}")
    except Exception as e:
        print(f"Direct API call failed: {e}")

    return None

# Scraping Fallback (Static & Dynamic)
def scrape_content(driver, url):
    # Static scrape
    headers = {"User-Agent": get_random_user_agent()}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        static_content = BeautifulSoup(response.content, "html.parser").get_text()
        print("Static content scrape succeeded.")
    except Exception as e:
        static_content = ""
        print(f"Static scrape failed: {e}")

    # Dynamic scrape
    try:
        dynamic_content = BeautifulSoup(driver.page_source, "html.parser").get_text()
        print("Dynamic content scrape succeeded.")
    except Exception as e:
        dynamic_content = ""
        print(f"Dynamic scrape failed: {e}")

    return f"Static:\n{static_content}\n\nDynamic:\n{dynamic_content}"

# Main Workflow
async def main(url):
    print(f"Checking {url} for API endpoint...")
    api_data = check_direct_api(url)
    if api_data:
        print("Processing API data...")
        print(api_data)
        return

    print("No API found. Proceeding with Selenium...")
    driver = start_selenium(url)
    try:
        content = scrape_content(driver, url)
        print(content)
    finally:
        driver.quit()

if __name__ == "__main__":
    target_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
    asyncio.run(main(target_url))
