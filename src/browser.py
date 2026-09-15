import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.config import PAGE_LOAD_TIMEOUT

logger = logging.getLogger(__name__)


def init_browser() -> webdriver.Chrome:
    """
    Initializes a visible Chrome/Chromium WebDriver instance with
    automation-hiding preferences to allow manual CAPTCHA solving.
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    try:
        # Use webdriver-manager to resolve matching chromedriver binary
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logger.warning(f"webdriver-manager fallback to built-in Selenium Manager: {e}")
        # Fallback to Selenium 4.x's built-in Selenium Manager
        driver = webdriver.Chrome(options=chrome_options)

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def close_browser(driver: webdriver.Chrome):
    """
    Safely terminates the browser driver session.
    """
    if driver:
        try:
            driver.quit()
        except Exception as e:
            logger.error(f"Error while closing browser session: {e}")