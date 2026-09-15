import logging
import os
import sys
from collections import defaultdict

from src.browser import close_browser, init_browser
from src.config import (
    INPUT_KEYWORDS_FILE,
    LOG_FILE,
    OUTPUT_DUPLICATES_FILE,
    OUTPUT_RESULTS_FILE,
    PORTAL_URL,
)
from src.paginator import paginate_and_extract
from src.search_flow import execute_keyword_search
from src.storage import (
    append_results,
    initialize_output_files,
    load_keywords,
    track_and_save_duplicates,
)


def setup_logging():
    """Configures dual logging to console and scraper.log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    setup_logging()
    logging.info("Starting SCP-Fetch Scraper...")

    # 1. Load keywords from input file
    keywords = load_keywords(INPUT_KEYWORDS_FILE)
    if not keywords:
        logging.error(f"No keywords found in '{INPUT_KEYWORDS_FILE}'. Exiting.")
        return

    print(f"\n=======================================================")
    print(f" SCP-Fetch Initialized: {len(keywords)} keywords loaded")
    print(f" Output Target: {OUTPUT_RESULTS_FILE}")
    print(f" Duplicate Tracker: {OUTPUT_DUPLICATES_FILE}")
    print(f"=======================================================\n")

    # 2. Reset / initialize output CSV files (Option C)
    initialize_output_files()

    # 3. In-memory duplicate tracker: case_id -> list of record dicts
    duplicate_index = defaultdict(list)

    # 4. Launch visible browser session
    driver = init_browser()
    driver.get(PORTAL_URL)

    total_extracted_count = 0

    try:
        for idx, kw in enumerate(keywords, 1):
            print(f"\n-------------------------------------------------------")
            print(f"[{idx}/{len(keywords)}] Processing Keyword: '{kw}'")
            print(f"-------------------------------------------------------")

            try:
                # Execute search with interactive CAPTCHA prompt
                has_results = execute_keyword_search(driver, kw)

                if not has_results:
                    continue

                # Paginate through all result pages for this keyword
                keyword_records = paginate_and_extract(driver, kw)
                total_extracted_count += len(keyword_records)

                # Persist records for this keyword immediately (end of pagination)
                append_results(keyword_records)

                # Update duplicate tracking report
                track_and_save_duplicates(duplicate_index, keyword_records)

                print(f"[✓] Completed keyword '{kw}' -> Saved {len(keyword_records)} records.")

            except Exception as kw_error:
                logging.error(f"Error processing keyword '{kw}': {kw_error}", exc_info=True)
                print(f"[!] Skipping to next keyword due to error.")

        print(f"\n=======================================================")
        print(f" All keywords processed successfully!")
        print(f" Total records extracted across all keywords: {total_extracted_count}")
        print(f" Main Results File: {OUTPUT_RESULTS_FILE}")
        print(f" Duplicates File:   {OUTPUT_DUPLICATES_FILE}")
        print(f"=======================================================\n")

    except KeyboardInterrupt:
        print("\n\n[!] Scraping process interrupted by operator (Ctrl+C).")
        print("[!] All data completed prior to this interruption has been safely saved.")
    except Exception as e:
        logging.exception(f"Unexpected fatal error occurred: {e}")
    finally:
        print("[*] Closing browser session...")
        close_browser(driver)
        logging.info("SCP-Fetch execution terminated.")


if __name__ == "__main__":
    main()