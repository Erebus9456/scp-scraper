import logging
from typing import Dict, List
from urllib.parse import urljoin

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from src.config import XPATH_DATA_ROWS, XPATH_GRIDVIEW_TABLE

logger = logging.getLogger(__name__)


def _extract_cell_text(row_elem, class_xpath: str, fallback_idx: int, cells: list) -> str:
    """
    Safely retrieves text using class locator or numeric column index fallback.
    """
    try:
        el = row_elem.find_element(By.XPATH, class_xpath)
        text = el.text.strip()
        if text:
            return text
    except NoSuchElementException:
        pass

    if fallback_idx < len(cells):
        try:
            return cells[fallback_idx].text.strip()
        except Exception:
            return ""
    return ""


def _extract_download_url(row_elem, cells: list, base_url: str) -> str:
    """
    Finds the PDF <a> element and resolves its absolute URL.
    """
    link_locators = [
        ".//a[contains(@class, 'download-link')]",
        ".//a[contains(@href, '.pdf') or contains(@href, 'Download')]",
        ".//td[contains(@class, 'download-cell')]//a",
        ".//td[10]//a"
    ]

    for loc in link_locators:
        try:
            link_el = row_elem.find_element(By.XPATH, loc)
            href = link_el.get_attribute("href")
            if href:
                return urljoin(base_url, href.strip())
        except NoSuchElementException:
            continue

    # Fallback to last cell if available
    if len(cells) >= 10:
        try:
            link_el = cells[9].find_element(By.XPATH, ".//a")
            href = link_el.get_attribute("href")
            if href:
                return urljoin(base_url, href.strip())
        except Exception:
            pass

    return ""


def extract_current_page_records(driver: WebDriver, keyword: str) -> List[Dict[str, str]]:
    """
    Extracts all valid judgment records from the currently loaded GridView page.
    """
    records: List[Dict[str, str]] = []
    current_url = driver.current_url

    # Locate all data rows in GridView
    try:
        rows = driver.find_elements(*XPATH_DATA_ROWS)
        if not rows:
            # Fallback if class names differ slightly
            rows = driver.find_elements(
                By.XPATH,
                '//table[contains(@id, "gvJudgments")]//tr[td and not(contains(@style, "pager")) and not(td/span[text()])]'
            )
    except Exception as e:
        logger.warning(f"Could not locate data rows: {e}")
        return records

    for row in rows:
        try:
            cells = row.find_elements(By.XPATH, "./td")
            # Must have sufficient columns (Sr No + 9 data columns)
            if len(cells) < 8:
                continue

            # Column 1: Sr No (skipped)
            # Column 2: Case Subject
            case_subject = _extract_cell_text(row, ".//td[contains(@class, 'subject-cell')]", 1, cells)
            # Column 3: Case No
            case_no = _extract_cell_text(row, ".//td[contains(@class, 'case-no')]", 2, cells)
            # Column 4: Case Title
            case_title = _extract_cell_text(row, ".//td[contains(@class, 'case-title')]", 3, cells)
            # Column 5: Author Judge
            author_judge = _extract_cell_text(row, ".//td[contains(@class, 'author-judge')]", 4, cells)
            # Column 6: Judgment Date
            judgment_date = _extract_cell_text(row, ".//td[6]", 5, cells)
            # Column 7: Upload Date
            upload_date = _extract_cell_text(row, ".//td[7]", 6, cells)
            # Column 8: Citation
            citation = _extract_cell_text(row, ".//td[8]", 7, cells)
            # Column 9: SC Citation
            sc_citation = _extract_cell_text(row, ".//td[9]", 8, cells)
            # Column 10: Download PDF link
            download_url = _extract_download_url(row, cells, current_url)

            # Only append if valid case data was retrieved
            if case_no or case_title or download_url:
                records.append({
                    "Keyword": keyword,
                    "Case Subject": case_subject,
                    "Case No": case_no,
                    "Case Title": case_title,
                    "Author Judge": author_judge,
                    "Judgment Date": judgment_date,
                    "Upload Date": upload_date,
                    "Citation": citation,
                    "SC Citation": sc_citation,
                    "Download": download_url
                })

        except StaleElementReferenceException:
            logger.warning("Encountered stale row element during extraction, skipping row.")
            continue
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            continue

    return records