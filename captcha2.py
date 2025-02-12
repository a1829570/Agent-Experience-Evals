import time
import os
import undetected_chromedriver as uc
from twocaptcha import TwoCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Load CAPTCHA solver API key
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")  # Set your API key as an environment variable
solver = TwoCaptcha(CAPTCHA_API_KEY)

# Function to solve reCAPTCHA v2/v3, hCaptcha, and Turnstile
def solve_captcha(driver, page_url):
    try:
        print("[INFO] Detecting CAPTCHA on the page...")

        # Look for reCAPTCHA, hCaptcha, or Cloudflare Turnstile
        captcha_elements = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
        if captcha_elements:
            print(f"[INFO] Found {len(captcha_elements)} CAPTCHA(s) on the page.")

            # Extract sitekey for CAPTCHA
            sitekey = driver.execute_script("""
                let captchaFrame = document.querySelector("iframe[src*='captcha']");
                if (captchaFrame) {
                    let src = captchaFrame.getAttribute("src");
                    let match = src.match(/k=([a-zA-Z0-9_-]+)/);
                    return match ? match[1] : null;
                }
                return null;
            """)

            if sitekey:
                print(f"[INFO] CAPTCHA sitekey detected: {sitekey}")

                # Solve CAPTCHA using 2Captcha API
                print("[INFO] Sending CAPTCHA for solving...")
                result = solver.recaptcha(sitekey=sitekey, url=page_url)

                if 'code' in result:
                    solved_token = result["code"]
                    print(f"[INFO] CAPTCHA solved successfully: {solved_token}")

                    # Inject the token into the page
                    driver.execute_script(f"""
                        let captchaInput = document.querySelector("textarea[name='g-recaptcha-response']");
                        if (!captchaInput) {{
                            captchaInput = document.createElement('textarea');
                            captchaInput.setAttribute('name', 'g-recaptcha-response');
                            captchaInput.style.display = 'none';
                            document.body.appendChild(captchaInput);
                        }}
                        captchaInput.value = arguments[0];
                    """, solved_token)

                    print("[INFO] Injected CAPTCHA token into the page.")

                    # Submit the form or refresh the page
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
                    time.sleep(5)  # Wait for the site to process
                    print("[SUCCESS] CAPTCHA bypassed!")

                    return True
                else:
                    print("[ERROR] Failed to solve CAPTCHA.")
                    return False
            else:
                print("[ERROR] No sitekey found on the page.")
                return False
        else:
            print("[INFO] No CAPTCHA detected on this page.")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during CAPTCHA solving: {e}")
        return False

# Launch browser and test CAPTCHA bypass
def start_browser(url):
    print(f"[INFO] Launching browser to access: {url}")

    # Configure Chrome options
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    # Solve CAPTCHA if present
    if solve_captcha(driver, url):
        print("[INFO] Continuing normal browsing...")
    else:
        print("[INFO] No CAPTCHA detected or solving failed.")

    input("[INFO] Press Enter to close the browser...")
    driver.quit()

# Example website with CAPTCHA (replace with the actual site you want to test)
test_url = "https://platform.openai.com/docs/bots/overview-of-openai-crawlers"
start_browser(test_url)
