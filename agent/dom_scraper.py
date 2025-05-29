import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import MoveTargetOutOfBoundsException

class DOMScraper:
    def __init__(self):
        pass

    def scrape_page(self, driver):
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
            driver.quit()

        print(static_status)
        print(dynamic_status)

        combined_content = static_content + "\n\n--- Dynamic Content ---\n\n" + dynamic_content
        return combined_content, static_status + "; " + dynamic_status

    async def scrape(self, driver):
        """Public interface for AX to call."""
        content, status = self.scrape_page(driver)
        return {
            "success": True if content else False,
            "friction": 1,
            "content": content,
            "status": status
        }
