import os
from selenium.webdriver.common.by import By

# ==========================================
# BASE PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_KEYWORDS_FILE = os.path.join(BASE_DIR, "data", "input", "keywords.csv")
OUTPUT_RESULTS_FILE = os.path.join(BASE_DIR, "data", "output", "judgments_results.csv")
OUTPUT_DUPLICATES_FILE = os.path.join(BASE_DIR, "data", "output", "duplicate_judgments.csv")
LOG_FILE = os.path.join(BASE_DIR, "logs", "scraper.log")

# ==========================================
# TARGET WEBSITE URL
# ==========================================
# Replace with the exact portal search URL if needed
PORTAL_URL = "https://scp.gov.pk/JudgmentsSearch"

# ==========================================
# TIMEOUT SETTINGS (in seconds)
# ==========================================
EXPLICIT_WAIT_TIMEOUT = 20
PAGE_LOAD_TIMEOUT = 60
POSTBACK_STABILIZATION_DELAY = 1.0

# ==========================================
# ELEMENT XPATHS
# ==========================================
# Search form elements
XPATH_KEYWORD_INPUT = (By.XPATH, '//*[@id="ContentPlaceHolder1_txtKeywords"]')
XPATH_SEARCH_BUTTON = (By.XPATH, '//*[@id="ContentPlaceHolder1_btnSearch"]')

# Zero-results detection
XPATH_NO_RECORDS = (
    By.XPATH,
    '//*[@id="ContentPlaceHolder1_pnlNoRecords"]//h4 | '
    '//h4[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "no judgments found")]'
)

# Results table / GridView elements
XPATH_GRIDVIEW_TABLE = (By.XPATH, '//table[contains(@id, "gvJudgments")]')
XPATH_DATA_ROWS = (By.XPATH, '//table[contains(@id, "gvJudgments")]//tr[contains(@class, "data-row")]')
XPATH_PAGINATION_ROW = (By.XPATH, '//table[contains(@id, "gvJudgments")]//tr[td/span or td/a[contains(@href, "Page$")]]')

# ==========================================
# CSV OUTPUT SCHEMA
# ==========================================
CSV_HEADERS_RESULTS = [
    "Keyword",
    "Case Subject",
    "Case No",
    "Case Title",
    "Author Judge",
    "Judgment Date",
    "Upload Date",
    "Citation",
    "SC Citation",
    "Download"
]

CSV_HEADERS_DUPLICATES = [
    "Case No",
    "Keywords Found In",
    "Case Title",
    "Download URL"
]