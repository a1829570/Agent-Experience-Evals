import time
import logging
import random
import platform
import subprocess

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from undetected_chromedriver import Chrome, ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

from agent.dom_scraper import DOMScraper
from form_handling.formdetection import fill_all_forms, gather_forms_from_dom

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

class BrowserController:
    def __init__(self):
        pass  # removed self.driver as it's now locally scoped

    @staticmethod
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

    def configure_driver(self):
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

        chrome_version = self.get_local_chrome_version()
        if not chrome_version:
            raise RuntimeError("Could not detect Chrome version.")

        version_main = int(chrome_version.split('.')[0])
        driver = Chrome(driver_executable_path=driver_path, options=options, version_main=version_main)
        return driver

    async def open(self, url, fill_forms=True):
        driver = None
        try:
            driver = self.configure_driver()
            print(f"[INFO] Launching browser to access: {url}")
            driver.get(url)

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("[INFO] Page loaded.")

            # Simulate human-like movement
            window_size = driver.get_window_size()
            actions = ActionChains(driver)
            for _ in range(random.randint(3, 7)):
                try:
                    actions.move_by_offset(
                        random.randint(-window_size["width"] // 2, window_size["width"] // 2),
                        random.randint(-window_size["height"] // 2, window_size["height"] // 2)
                    ).perform()
                    time.sleep(random.uniform(0.5, 1.2))
                except MoveTargetOutOfBoundsException:
                    continue

            # Detect forms
            forms = gather_forms_from_dom(driver)
            if forms:
                print(f"[INFO] {len(forms)} form(s) detected on the page.")
                if fill_forms:
                    user_input = input("Form(s) found. Do you want to fill them? (y/n): ").strip().lower()
                    if user_input == "y":
                        fill_all_forms(driver)
                    else:
                        print("[INFO] Skipping form filling as per user input.")

            # Scrape DOM content
            scraper = DOMScraper()
            content, _ = scraper.scrape_page(driver)

            return {
                "content": content,
                "status": "Completed",
                "success": bool(content and content.strip())
            }

        except TimeoutException:
            print(f"[ERROR] Timeout while loading {url}")
            return {"success": False, "status": "Timeout", "content": ""}

        except Exception as e:
            print(f"[ERROR] Exception during browser session: {e}")
            return {"success": False, "status": str(e), "content": ""}

        finally:
            if driver:
                driver.quit()
