import csv
import logging
import os
from typing import Dict, List

from src.config import (
    CSV_HEADERS_DUPLICATES,
    CSV_HEADERS_RESULTS,
    INPUT_KEYWORDS_FILE,
    OUTPUT_DUPLICATES_FILE,
    OUTPUT_RESULTS_FILE,
)

logger = logging.getLogger(__name__)


def load_keywords(file_path: str = INPUT_KEYWORDS_FILE) -> List[str]:
    """
    Loads keywords from CSV or text file.
    Creates a sample file if it does not already exist.
    """
    keywords = []

    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["keyword"])
            writer.writerow(["PEMRA"])
            writer.writerow(["NAB"])
        logger.info(f"Created sample keywords file at '{file_path}'.")
        return ["PEMRA", "NAB"]

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            word = row[0].strip()
            # Ignore header if present
            if word and word.lower() != "keyword":
                keywords.append(word)

    logger.info(f"Loaded {len(keywords)} keywords from '{file_path}'.")
    return keywords


def initialize_output_files():
    """
    Initializes/resets output CSV files with headers at the start of a run (Option C).
    """
    os.makedirs(os.path.dirname(OUTPUT_RESULTS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_DUPLICATES_FILE), exist_ok=True)

    # Initialize main results file
    with open(OUTPUT_RESULTS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS_RESULTS)

    # Initialize duplicates tracking file
    with open(OUTPUT_DUPLICATES_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS_DUPLICATES)

    logger.info("Initialized output CSV files with headers.")


def append_results(records: List[Dict[str, str]]):
    """
    Appends a list of judgment records to the main CSV file.
    """
    if not records:
        return

    with open(OUTPUT_RESULTS_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for r in records:
            writer.writerow([
                r.get("Keyword", ""),
                r.get("Case Subject", ""),
                r.get("Case No", ""),
                r.get("Case Title", ""),
                r.get("Author Judge", ""),
                r.get("Judgment Date", ""),
                r.get("Upload Date", ""),
                r.get("Citation", ""),
                r.get("SC Citation", ""),
                r.get("Download", "")
            ])

    logger.info(f"Appended {len(records)} records to '{OUTPUT_RESULTS_FILE}'.")


def track_and_save_duplicates(
    all_records_by_case: Dict[str, List[Dict[str, str]]],
    new_records: List[Dict[str, str]]
):
    """
    Updates the in-memory duplicate tracker and writes out the duplicates CSV
    linking Case No to all keywords that matched it.
    """
    for r in new_records:
        case_id = r.get("Case No", "").strip() or r.get("Download", "").strip()
        if case_id:
            all_records_by_case[case_id].append(r)

    # Write duplicates to file
    with open(OUTPUT_DUPLICATES_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS_DUPLICATES)

        for case_id, entries in all_records_by_case.items():
            keywords_found = sorted(list({e["Keyword"] for e in entries if e.get("Keyword")}))
            if len(keywords_found) > 1:
                sample = entries[0]
                writer.writerow([
                    case_id,
                    ", ".join(keywords_found),
                    sample.get("Case Title", ""),
                    sample.get("Download", "")
                ])