import csv
from pathlib import Path


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
OUTPUT_DIR = BASE_DIR / "data" / "output"

# Input files
INPUT_FILES = [
    OUTPUT_DIR / "judgments_results_A_M.csv",
    OUTPUT_DIR / "judgments_results_N_T.csv",
    OUTPUT_DIR / "judgments_results_U_Z.csv",
]

# Output file
OUTPUT_FILE = OUTPUT_DIR / "judgments_results.csv"

# Expected columns
FIELDNAMES = [
    "Keyword",
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


def merge_csv_files():
    total_rows = 0

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for input_file in INPUT_FILES:
            if not input_file.exists():
                print(f"[ERROR] File not found: {input_file}")
                continue

            file_rows = 0

            with input_file.open("r", newline="", encoding="utf-8-sig") as infile:
                reader = csv.DictReader(infile)

                # Validate columns
                if reader.fieldnames != FIELDNAMES:
                    print(f"[WARNING] Column mismatch in: {input_file}")
                    print(f"Expected: {FIELDNAMES}")
                    print(f"Found:    {reader.fieldnames}")

                for row in reader:
                    writer.writerow(row)
                    file_rows += 1
                    total_rows += 1

            print(f"[OK] {input_file.name}: {file_rows:,} rows")

    print()
    print(f"[DONE] Merged {total_rows:,} rows")
    print(f"[OUTPUT] {OUTPUT_FILE}")


if __name__ == "__main__":
    merge_csv_files()