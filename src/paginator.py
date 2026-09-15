import logging
import time
from typing import Dict, List

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config import (
    EXPLICIT_WAIT_TIMEOUT,
    POSTBACK_STABILIZATION_DELAY,
    XPATH_GRIDVIEW_TABLE,
    XPATH_PAGINATION_ROW,
)
from src.extractor import extract_current_page_records

logger = logging.getLogger(__name__)


def paginate_and_extract(driver: WebDriver, keyword: str) -> List[Dict[str, str]]:
    """
    Iterates through all result pages for a keyword and extracts all records.
    Handles dynamic page numbers and '...' page window jumps.
    """
    all_keyword_records: List[Dict[str, str]] = []
    page_counter = 1

    while True:
        # 1. Ensure the GridView table is present
        try:
            WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located(XPATH_GRIDVIEW_TABLE)
            )
        except TimeoutException:
            logger.warning(f"Timed out waiting for GridView table on page {page_counter}.")
            break

        # 2. Extract records from the currently visible page
        page_records = extract_current_page_records(driver, keyword)
        all_keyword_records.extend(page_records)
        print(f"   -> Page {page_counter}: Extracted {len(page_records)} records.")

        # 3. Locate pagination controls
        pagination_rows = driver.find_elements(*XPATH_PAGINATION_ROW)
        if not pagination_rows:
            # Single page result set (no pagination row rendered)
            print("   -> Single page results (no further pages).")
            break

        pager_row = pagination_rows[-1]

        # 4. Determine current active page number from <span>
        try:
            current_span = pager_row.find_element(By.XPATH, ".//td/span")
            current_page_num = int(current_span.text.strip())
        except (NoSuchElementException, ValueError):
            logger.info("No active page <span> found in pager row. Pagination complete.")
            break

        next_target_num = current_page_num + 1

        # 5. Check if numeric next page link is directly visible
        next_link = None
        direct_links = pager_row.find_elements(
            By.XPATH, f".//td/a[normalize-space(text())='{next_target_num}']"
        )

        if direct_links:
            next_link = direct_links[0]
            print(f"   -> Clicking next numeric page link: {next_target_num}")
        else:
            # 6. If numeric link not in current window, check for forward '...' link
            # We look for '...' inside a <td> that appears AFTER the active <span>
            forward_dots = pager_row.find_elements(
                By.XPATH, ".//td[span]/following-sibling::td/a[normalize-space(text())='...']"
            )
            if forward_dots:
                next_link = forward_dots[0]
                print(f"   -> Page {next_target_num} outside visible window. Clicking forward '...'")
            else:
                print(f"   -> Reached final page ({current_page_num}). Pagination finished.")
                break

        # 7. Execute navigation click and wait for ASP.NET postback update
        try:
            current_table = driver.find_element(*XPATH_GRIDVIEW_TABLE)

            try:
                next_link.click()
            except ElementClickInterceptedException:
                # Fallback to JavaScript click if intercepted by an overlay
                driver.execute_script("arguments[0].click();", next_link)

            # Wait until the previous table is destroyed by the postback
            WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
                EC.staleness_of(current_table)
            )
            # Wait until the new GridView table is rendered
            WebDriverWait(driver, EXPLICIT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located(XPATH_GRIDVIEW_TABLE)
            )

            time.sleep(POSTBACK_STABILIZATION_DELAY)
            page_counter += 1

        except TimeoutException:
            logger.error(f"Timeout while waiting for postback after clicking page {next_target_num}.")
            break
        except Exception as e:
            logger.error(f"Error during pagination transition: {e}")
            break

    return all_keyword_records