import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

import logging

def suppress_seleniumwire_logs_during_input():
    """
    Helper to temporarily suppress seleniumwire logs while user is typing.
    """
    sw_logger = logging.getLogger("seleniumwire")
    old_level = sw_logger.level
    sw_logger.setLevel(logging.CRITICAL)
    return old_level  # We’ll restore it manually later


class BrowserController:
    def __init__(self):
        self.driver = None

    def configure_driver(self):
        """Configures an undetected ChromeDriver with stealth settings."""
        options = Options()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={USER_AGENT}")
        options.add_argument("--disable-webrtc")

        chrome_executable_path = ChromeDriverManager().install()
        print(f"[INFO] Using ChromeDriver: {chrome_executable_path}")

        driver = uc.Chrome(driver_executable_path=chrome_executable_path, options=options)
        return driver

    def open(self, url):
        """Launches the browser and performs human-like movements to reduce detection."""
        print(f"[INFO] Launching browser to access: {url}")
        self.driver = self.configure_driver()
        self.driver.get(url)
        time.sleep(5)  # Let the page load

        # Human-like random motion
        window_size = self.driver.get_window_size()
        width, height = window_size["width"], window_size["height"]
        actions = ActionChains(self.driver)

        for _ in range(random.randint(3, 7)):
            x_offset = random.randint(-width // 2, width // 2)
            y_offset = random.randint(-height // 2, height // 2)
            try:
                actions.move_by_offset(x_offset, y_offset).perform()
                time.sleep(random.uniform(0.5, 1.2))
            except MoveTargetOutOfBoundsException:
                pass

        return self.driver

    def close(self):
        """Clean up browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None
