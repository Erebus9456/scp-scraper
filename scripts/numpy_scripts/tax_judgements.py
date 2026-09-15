import csv
import re
from pathlib import Path


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Input / output files
INPUT_FILE = BASE_DIR / "data" / "output" / "unique_judgements.csv"
OUTPUT_FILE = BASE_DIR / "data" / "output" / "tax_judgements.csv"


# Terms related to FBR, taxation, income tax, etc.
TAX_PATTERNS = [
    # FBR
    r"\bfbr\b",
    r"federal board of revenue",

    # Income tax
    r"income tax",
    r"income-tax",
    r"incometax",
    r"income taxation",

    # General taxation
    r"\btax\b",
    r"\btaxation\b",
    r"taxable",
    r"taxpayer",
    r"taxpayers",
    r"tax liability",
    r"tax liabilities",
    r"tax assessment",
    r"tax assessments",
    r"tax return",
    r"tax returns",
    r"tax evasion",
    r"tax fraud",
    r"tax recovery",
    r"tax demand",
    r"tax notice",
    r"tax authority",
    r"tax authorities",

    # Sales tax
    r"sales tax",
    r"sales-tax",
    r"sales taxation",

    # Federal excise
    r"federal excise",
    r"federal excise duty",
    r"\bfed\b.*\bexcise\b",
    r"excise duty",

    # Withholding
    r"withholding tax",
    r"withholding-tax",
    r"withholding",

    # Customs / revenue
    r"customs duty",
    r"customs duties",
    r"customs",
    r"customs act",
    r"revenue",
    r"revenue authority",
    r"revenue department",

    # Pakistan tax legislation / terminology
    r"income tax ordinance",
    r"income tax act",
    r"sales tax act",
    r"sales tax ordinance",
    r"federal excise act",
    r"finance act",
    r"finance bill",

    # Common Pakistani tax terms
    r"additional tax",
    r"advance tax",
    r"capital gains tax",
    r"capital gain",
    r"minimum tax",
    r"super tax",
    r"turnover tax",
    r"presumptive tax",
    r"advance income tax",
    r"withholding agent",
    r"withholding agent",

    # Tax tribunals / appeals
    r"appellate tribunal.*inland revenue",
    r"appellate tribunal.*tax",
    r"inland revenue",
    r"commissioner.*inland revenue",
    r"commissioner.*income tax",
    r"collector.*customs",
]


# Compile once for faster matching
TAX_REGEX = re.compile(
    "|".join(f"(?:{pattern})" for pattern in TAX_PATTERNS),
    re.IGNORECASE,
)


def is_tax_related(case_subject):
    """Return True if Case Subject is related to taxation/FBR."""
    if not case_subject:
        return False

    return bool(TAX_REGEX.search(case_subject))


def extract_tax_judgements():
    total_count = 0
    matched_count = 0

    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as infile, OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as outfile:

        reader = csv.DictReader(infile)

        if "Case Subject" not in reader.fieldnames:
            raise ValueError(
                "The input CSV does not contain a 'Case Subject' column."
            )

        # Keep all columns
        writer = csv.DictWriter(
            outfile,
            fieldnames=reader.fieldnames
        )

        writer.writeheader()

        for row in reader:
            total_count += 1

            case_subject = row.get("Case Subject", "")

            if is_tax_related(case_subject):
                writer.writerow(row)
                matched_count += 1

    print("=" * 55)
    print("TAX / FBR JUDGEMENT EXTRACTION")
    print("=" * 55)
    print(f"Total unique judgements : {total_count:,}")
    print(f"Tax-related judgements  : {matched_count:,}")
    print(f"Output file             : {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    extract_tax_judgements()