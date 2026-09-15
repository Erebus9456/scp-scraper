import logging
import time

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config import (
    EXPLICIT_WAIT_TIMEOUT,
    XPATH_GRIDVIEW_TABLE,
    XPATH_KEYWORD_INPUT,
    XPATH_NO_RECORDS,
    XPATH_SEARCH_BUTTON,
)

logger = logging.getLogger(__name__)


def _safe_input_text(driver: WebDriver, element, text: str):
    """
    Safely clears and enters text into an input element using standard
    Selenium methods with a JavaScript fallback if the element is obstructed.
    """
    # Scroll element to the center of the viewport
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
    time.sleep(0.3)

    try:
        element.click()
        element.clear()
        element.send_keys(text)
    except (ElementNotInteractableException, ElementClickInterceptedException):
        logger.warning("Standard clear/send_keys blocked. Using JavaScript injection fallback.")
        driver.execute_script("""
            arguments[0].value = '';
            arguments[0].focus();
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, element, text)


def execute_keyword_search(driver: WebDriver, keyword: str) -> bool:
    """
    Clears the search input, enters the keyword, pauses execution for manual
    CAPTCHA solving, submits the search form, and checks for results.

    Returns:
        bool: True if results are loaded and ready for scraping,
              False if 'No Judgments Found' or an error occurs.
    """
    # 1. Wait for document to be ready
    try:
        WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        logger.warning("Page readyState check timed out, proceeding to find elements...")

    # 2. Locate keyword input box (wait until clickable/interactable)
    try:
        search_input = WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(XPATH_KEYWORD_INPUT)
        )
        _safe_input_text(driver, search_input, keyword)
    except TimeoutException:
        # Fallback search if XPath didn't become clickable in time
        try:
            search_input = driver.find_element(*XPATH_KEYWORD_INPUT)
            _safe_input_text(driver, search_input, keyword)
        except Exception as e:
            logger.error(f"Could not locate or interact with keyword input box: {e}")
            return False

    # 3. Interactive CAPTCHA prompt
    print("\n" + "=" * 60)
    print(f" [ACTION REQUIRED] Solving search for keyword: '{keyword}'")
    print(" 1. Look at the open Chrome browser window.")
    print(" 2. Solve the CAPTCHA challenge.")
    print(" 3. Return to this terminal and press [ENTER] to execute search.")
    print("=" * 60)

    input(" >> Press [ENTER] after solving CAPTCHA: ")

    # 4. Locate and click Search button
    try:
        search_button = WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(XPATH_SEARCH_BUTTON)
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        time.sleep(0.2)

        try:
            search_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", search_button)

        print("   [*] Search submitted. Waiting for portal response...")
    except TimeoutException:
        logger.error("Could not find or click the search button.")
        return False

    # 5. Wait for either results table or 'No Records' message to appear
    time.sleep(2)  # Stabilization buffer for network response

    start_time = time.time()
    while time.time() - start_time < EXPLICIT_WAIT_TIMEOUT:
        # Check for 'No Judgments Found' panel
        no_records_elements = driver.find_elements(*XPATH_NO_RECORDS)
        for el in no_records_elements:
            try:
                if el.is_displayed() and "no" in el.text.lower():
                    print(f"   [-] No Judgments Found for keyword: '{keyword}'")
                    return False
            except Exception:
                pass

        # Check for results GridView table
        grid_elements = driver.find_elements(*XPATH_GRIDVIEW_TABLE)
        for grid in grid_elements:
            try:
                if grid.is_displayed():
                    print(f"   [✓] Results table loaded successfully for '{keyword}'.")
                    return True
            except Exception:
                pass

        time.sleep(1)

    logger.warning("Timed out waiting for response state (neither results table nor no-records found).")
    return False