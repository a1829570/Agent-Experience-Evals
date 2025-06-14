import logging
import random
import time
from typing import Optional, List, Tuple

# BeautifulSoup for post-JavaScript HTML parsing
from bs4 import BeautifulSoup

# Selenium imports
import undetected_chromedriver as uc
from seleniumwire import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    MoveTargetOutOfBoundsException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ------------------------------------
# Configure Logging (optional)
# ------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)
logging.getLogger("seleniumwire").setLevel(logging.WARNING)
# ------------------------------------
# Start Selenium (Undetected Chrome) with "humanlike" moves
# ------------------------------------
def start_selenium_with_wire(url: str):
    """
    Launches an undetected Chrome session with:
      - Basic stealth
      - 'Humanlike' random mouse movements
    """
    options = uc.ChromeOptions()
    # If you want headless, uncomment:
    # options.add_argument("--headless")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")

    # Install and set up the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(
        service=service,
        seleniumwire_options={},  # Extra config if needed
        options=options,
    )

    driver.get(url)
    logger.info("Navigated to %s", url)

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

# ------------------------------------
# HELPER: Locate a field in the live DOM using fallback strategies
# ------------------------------------
def locate_field(driver, field_identifier: str) -> Optional[WebElement]:
    """
    Tries multiple locators to find an element for the given field_identifier.
    Returns the WebElement if found, otherwise None.
    """

    # 1) Try By.NAME
    try:
        elm = driver.find_element(By.NAME, field_identifier)
        return elm
    except NoSuchElementException:
        pass

    # 2) Try By.ID
    try:
        elm = driver.find_element(By.ID, field_identifier)
        return elm
    except NoSuchElementException:
        pass

    # 3) Try placeholder
    #   input[placeholder='<val>'], textarea[placeholder='<val>']
    try:
        css_selector = f"input[placeholder='{field_identifier}'], textarea[placeholder='{field_identifier}'], select[placeholder='{field_identifier}']"
        elm = driver.find_element(By.CSS_SELECTOR, css_selector)
        return elm
    except NoSuchElementException:
        pass

    # 4) Try aria-label
    try:
        css_selector = f"input[aria-label='{field_identifier}'], textarea[aria-label='{field_identifier}'], select[aria-label='{field_identifier}']"
        elm = driver.find_element(By.CSS_SELECTOR, css_selector)
        return elm
    except NoSuchElementException:
        pass

    # 5) Try partial fallback in the entire DOM (risky if multiple matches)
    #    e.g. find any input containing the identifier in its placeholder or name
    #    This is purely optional. For broad coverage, uncomment:

    # from selenium.common.exceptions import WebDriverException
    # try:
    #     all_inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
    #     for i in all_inputs:
    #         placeholder = i.get_attribute("placeholder") or ""
    #         name = i.get_attribute("name") or ""
    #         aria_label = i.get_attribute("aria-label") or ""
    #         if field_identifier in placeholder or field_identifier == name or field_identifier in aria_label:
    #             return i
    # except WebDriverException:
    #     pass

    # If none worked, return None
    return None

# ------------------------------------
# HELPER: Possibly handle Shadow DOM (Optional)
# ------------------------------------
def locate_field_in_shadow_root(driver, shadow_host_selector: str, inner_selector: str) -> Optional[WebElement]:
    """
    Example logic to locate a field if it's in a shadow root.
    shadow_host_selector is the CSS of the custom element that hosts the shadow root.
    inner_selector is what to find inside the shadow root.

    If your forms are inside shadow DOM, you must do something like this manually.
    """
    try:
        host = driver.find_element(By.CSS_SELECTOR, shadow_host_selector)
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
        if shadow_root:
            return shadow_root.find_element(By.CSS_SELECTOR, inner_selector)
    except Exception as e:
        logger.warning(f"Shadow root locate failed: {e}")
    return None

# ------------------------------------
# Step 1: Gather all forms from the rendered DOM (post-JS)
# ------------------------------------
def gather_forms_from_dom(driver):
    """
    Waits for form tags in the live DOM, then uses BeautifulSoup to parse them.
    Returns a list of <form> elements as BeautifulSoup objects.
    """
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "form"))
        )
        time.sleep(2)  # Additional buffer for JS rendering
    except TimeoutException:
        logger.warning("No <form> elements found within 15 seconds.")
        return []

    # Parse the rendered HTML with BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    forms = soup.find_all("form")
    return forms

# ------------------------------------
# Step 2: Detect fields in a single <form> by multiple attributes
# ------------------------------------
def detect_fields_in_form(form) -> List[Tuple[str, str]]:
    """
    form: a BeautifulSoup <form> element
    Returns a list of (best_identifier, field_type) for each input-like element.
    """
    fields = []
    inputs = form.find_all(["input", "textarea", "select"])
    for i, inp in enumerate(inputs):
        # Gather possible attributes
        name_attr = inp.get("name")
        id_attr = inp.get("id")
        placeholder_attr = inp.get("placeholder")
        aria_label_attr = inp.get("aria-label")
        # Priority-based fallback for a 'best identifier'
        best_identifier = name_attr or id_attr or placeholder_attr or aria_label_attr or f"unnamed-{i}"

        # Type defaults to 'text' if not present
        field_type = inp.get("type", "text")
        fields.append((best_identifier, field_type))
    return fields

# ------------------------------------
# Step 3: Fill each field in the live DOM
# ------------------------------------
def fill_field(driver, field_identifier: str, value: str):
    """
    Attempts to locate the field with fallback locators, waits for it to be clickable,
    then sends the value. If that fails, tries a JS fallback.
    """
    logger.info(f"Filling field '{field_identifier}' with '{value}'")
    elm = locate_field(driver, field_identifier)

    if elm is None:
        logger.error(f"Could not locate field '{field_identifier}' in the DOM.")
        return

    # Ensure clickable
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(elm))
    except TimeoutException:
        logger.warning(f"Field '{field_identifier}' not clickable, attempting direct JS fallback.")
        # Attempt fallback below
        pass

    # Try standard Selenium fill
    try:
        elm.clear()
        elm.send_keys(value)
        logger.info(f"Selenium input succeeded for '{field_identifier}'")
    except Exception as e:
        logger.error(f"Selenium input failed for '{field_identifier}': {e}")
        logger.info("Attempting JavaScript fallback...")

        # JavaScript fallback
        try:
            driver.execute_script(
                "arguments[0].value = arguments[1];",
                elm,
                value
            )
            logger.info(f"JavaScript fallback succeeded for '{field_identifier}'")
        except Exception as js_e:
            logger.error(f"JavaScript fallback also failed for '{field_identifier}': {js_e}")

# ------------------------------------
# Step 4: Submit a form
# ------------------------------------
def submit_form(driver, form_index=1):
    """
    Tries to find a <button or <input> with type='submit' in the DOM.
    If not found, does a JS submission of the first <form>.
    Note: Optionally, we can limit to 'nth' form if needed.
    """
    try:
        # This simplistic approach finds the FIRST submit button in the page
        # or an input with type=submit
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
        submit_btn.click()
        logger.info(f"Form {form_index} submitted by clicking the submit button.")
    except Exception as e:
        logger.warning(f"No submit button found for form {form_index}, attempting JS submit: {e}")
        try:
            driver.execute_script("document.querySelector('form').submit();")
            logger.info(f"Form {form_index} submitted via JavaScript.")
        except Exception as js_e:
            logger.error(f"JavaScript form submission failed for form {form_index}: {js_e}")

# ------------------------------------
# Orchestrate the entire form-filling flow
# ------------------------------------
def fill_all_forms(driver):
    """
    1. Locate all forms in the rendered DOM.
    2. For each form, detect fields.
    3. Prompt user for values (or auto-fill).
    4. Fill each field.
    5. Submit.
    """
    forms = gather_forms_from_dom(driver)
    if not forms:
        logger.info("No forms found on the page.")
        return

    logger.info(f"Found {len(forms)} form(s) on the page.")

    for idx, form in enumerate(forms, start=1):
        logger.info(f"\n[FORM {idx}]")
        action = form.get("action", "No action specified")
        method = form.get("method", "GET")
        logger.info(f"Action: {action}")
        logger.info(f"Method: {method}")

        # Gather fields from the <form>
        fields = detect_fields_in_form(form)
        if not fields:
            logger.info("No detectable fields found in this form.")
            continue

        logger.info("Detected Fields:")
        for (identifier, ftype) in fields:
            logger.info(f" - {identifier} ({ftype})")

        # Ask user for each field's input
        field_values = {}
        for (identifier, ftype) in fields:
            # Only ask for these types; skip e.g. hidden or checkboxes
            if ftype in ["text", "password", "email", "textarea"]:
                user_val = input(f"Enter value for '{identifier}' ({ftype}): ")
                field_values[identifier] = user_val

        # Fill each field
        for f_id, val in field_values.items():
            fill_field(driver, f_id, val)

        # Finally, submit the form
        submit_form(driver, form_index=idx)

# ------------------------------------
# Main
# ------------------------------------
if __name__ == "__main__":
    # Replace with whatever URL you want to test
    target_url = "https://wigwh6wyjpvepudb.vercel.app"

    # Start the driver
    driver = start_selenium_with_wire(target_url)

    # Fill all forms
    fill_all_forms(driver)

    # Close the browser
    driver.quit()
    logger.info("Done.")
