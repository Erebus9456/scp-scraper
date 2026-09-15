import csv
from pathlib import Path


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Paths
INPUT_FILE = BASE_DIR / "data" / "output" / "judgments_results.csv"
OUTPUT_FILE = BASE_DIR / "data" / "output" / "unique_judgements.csv"

# Columns to keep (Keyword removed)
OUTPUT_COLUMNS = [
    "Case Subject",
    "Case No",
    "Case Title",
    "Author Judge",
    "Judgment Date",
    "Upload Date",
    "Citation",
    "SC Citation",
    "Download",
]


def extract_unique_judgements():
    seen_urls = set()
    unique_count = 0
    duplicate_count = 0

    with INPUT_FILE.open("r", newline="", encoding="utf-8-sig") as infile, \
         OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=OUTPUT_COLUMNS)

        writer.writeheader()

        for row in reader:
            pdf_url = row["Download"].strip()

            # Skip rows without a PDF URL
            if not pdf_url:
                continue

            # Duplicate judgment
            if pdf_url in seen_urls:
                duplicate_count += 1
                continue

            # New unique judgment
            seen_urls.add(pdf_url)

            output_row = {
                column: row.get(column, "")
                for column in OUTPUT_COLUMNS
            }

            writer.writerow(output_row)
            unique_count += 1

    print("=" * 50)
    print("UNIQUE JUDGEMENT EXTRACTION")
    print("=" * 50)
    print(f"Unique judgements : {unique_count:,}")
    print(f"Duplicates removed: {duplicate_count:,}")
    print(f"Output file       : {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    extract_unique_judgements()