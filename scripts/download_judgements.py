import csv
import re
import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = (
    BASE_DIR
    / "data"
    / "output"
    / "tax_judgements.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "judgements_pdf"
)

FAILED_FILE = (
    BASE_DIR
    / "data"
    / "failed_downloads.csv"
)


# Number of simultaneous Selenium tabs.
#
# Start conservatively because the Supreme Court site
# is behind Akamai.
#
# Increase to 4 or 5 if everything remains stable.
CONCURRENT_TABS = 3


# Maximum attempts for a failed PDF.
MAX_RETRIES = 3


# How long to wait for a PDF download.
DOWNLOAD_TIMEOUT = 120


# How frequently the download directory is checked.
POLL_INTERVAL = 0.25


# Browser user agent.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


# ============================================================
# FILE HELPERS
# ============================================================

def sanitize_filename(value):
    """
    Make a string safe for macOS/Linux filenames.
    """

    value = str(value or "").strip()

    value = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "_",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = value.strip(" .")

    return value[:200]


def get_filename(row):
    """
    Generate a stable filename.

    Prefer Case No because it should uniquely identify
    the judgment.
    """

    case_no = (
        row.get("Case No")
        or ""
    ).strip()

    if case_no:

        filename = sanitize_filename(
            case_no
        )

    else:

        filename = sanitize_filename(
            row.get("Case Title")
            or row.get("Case Subject")
            or "judgement"
        )

    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    return filename


def is_valid_pdf(path):
    """
    Check that the file exists and contains an actual PDF.
    """

    if not path.exists():
        return False

    try:

        if path.stat().st_size < 100:
            return False

        with open(path, "rb") as f:
            header = f.read(5)

        return header == b"%PDF-"

    except OSError:
        return False


# ============================================================
# CSV
# ============================================================

def load_rows():
    """
    Load rows from the input CSV.
    """

    rows = []

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:

        reader = csv.DictReader(f)

        if "Download" not in reader.fieldnames:
            raise RuntimeError(
                "CSV does not contain a 'Download' column."
            )

        for row in reader:

            url = (
                row.get("Download")
                or ""
            ).strip()

            if not url:
                continue

            rows.append(row)

    return rows


# ============================================================
# CHROME
# ============================================================

def create_driver(download_dir):
    """
    Create a Selenium Chrome instance configured to
    download PDFs instead of opening Chrome's PDF viewer.
    """

    options = Options()

    # Headless production mode.
    options.add_argument("--headless=new")

    options.add_argument(
        "--window-size=1920,1080"
    )

    options.add_argument(
        f"--user-agent={USER_AGENT}"
    )

    # Important for the Supreme Court PDF behavior.
    options.add_argument(
        "--disable-pdf-extension"
    )

    # Avoid automation-related Chrome behavior where possible.
    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    # Stability.
    options.add_argument(
        "--disable-dev-shm-usage"
    )

    options.add_argument(
        "--no-sandbox"
    )

    # Chrome download configuration.
    prefs = {

        # Automatically download.
        "download.prompt_for_download": False,

        # Do not ask where to save.
        "download.directory_upgrade": True,

        # CRITICAL:
        # Open PDF externally instead of Chrome PDF viewer.
        "plugins.always_open_pdf_externally": True,

        # Do not show download UI.
        "download.show_downloads": False,

        # Make sure downloads are allowed.
        "safebrowsing.enabled": True,
    }

    options.add_experimental_option(
        "prefs",
        prefs,
    )

    driver = webdriver.Chrome(
        options=options
    )

    # Explicitly allow downloads in headless Chrome.
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {
            "behavior": "allow",
            "downloadPath": str(download_dir),
        },
    )

    return driver


# ============================================================
# DOWNLOAD DETECTION
# ============================================================

def wait_for_download(
    download_dir,
    expected_filename,
    timeout,
):
    """
    Wait until Chrome finishes downloading the expected PDF.
    """

    expected_path = (
        download_dir
        / expected_filename
    )

    partial_path = (
        download_dir
        / f"{expected_filename}.crdownload"
    )

    start = time.monotonic()

    while (
        time.monotonic() - start
        < timeout
    ):

        # Finished download.
        if expected_path.exists():

            # Make sure Chrome has finished writing.
            if not partial_path.exists():

                # Give filesystem a moment.
                time.sleep(0.1)

                if is_valid_pdf(
                    expected_path
                ):
                    return expected_path

        # Chrome may use a temporary filename.
        #
        # This is useful when the server specifies a different
        # Content-Disposition filename.
        partial_files = list(
            download_dir.glob(
                "*.crdownload"
            )
        )

        if not partial_files:

            # Look for recently-created PDFs.
            pdf_files = list(
                download_dir.glob("*.pdf")
            )

            for pdf in pdf_files:

                if is_valid_pdf(pdf):

                    # If it isn't already our expected filename,
                    # move it to the expected name.
                    if pdf != expected_path:

                        try:

                            if expected_path.exists():
                                expected_path.unlink()

                            pdf.rename(
                                expected_path
                            )

                        except OSError:
                            continue

                    return expected_path

        time.sleep(
            POLL_INTERVAL
        )

    return None


# ============================================================
# SINGLE DOWNLOAD
# ============================================================

def download_one(
    driver,
    row,
    download_dir,
):
    """
    Download a single PDF using Selenium.
    """

    url = (
        row.get("Download")
        or ""
    ).strip()

    filename = get_filename(row)

    output_path = (
        download_dir
        / filename
    )

    # Already downloaded.
    if is_valid_pdf(output_path):
        return True, "already_exists"

    # Remove stale partial file.
    partial = (
        download_dir
        / f"{filename}.crdownload"
    )

    if partial.exists():

        try:
            partial.unlink()
        except OSError:
            pass

    try:

        # Navigate to PDF.
        driver.get(url)

        # Wait until Chrome finishes downloading.
        downloaded = wait_for_download(
            download_dir,
            filename,
            DOWNLOAD_TIMEOUT,
        )

        if downloaded is None:

            return (
                False,
                "Download timeout",
            )

        # Final validation.
        if not is_valid_pdf(
            downloaded
        ):

            try:
                downloaded.unlink()
            except OSError:
                pass

            return (
                False,
                "Downloaded file is not a valid PDF",
            )

        return True, "downloaded"

    except Exception as e:

        return (
            False,
            f"{type(e).__name__}: {e}",
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print(" Supreme Court of Pakistan — PDF Downloader")
    print("=" * 72)
    print()

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not CSV_FILE.exists():

        raise FileNotFoundError(
            f"Input CSV not found:\n{CSV_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = load_rows()

    print(
        f"Input CSV       : {CSV_FILE}"
    )

    print(
        f"Total CSV rows  : {len(rows)}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    print(
        f"Concurrent tabs : {CONCURRENT_TABS}"
    )

    print(
        f"Max retries     : {MAX_RETRIES}"
    )

    print()

    # --------------------------------------------------------
    # Build queue
    # --------------------------------------------------------

    pending = []

    skipped = 0

    for row in rows:

        filename = get_filename(row)

        path = (
            OUTPUT_DIR
            / filename
        )

        if is_valid_pdf(path):

            skipped += 1

        else:

            pending.append(row)

    print(
        f"Already valid   : {skipped}"
    )

    print(
        f"Pending         : {len(pending)}"
    )

    print()

    if not pending:

        print(
            "Nothing to download."
        )

        return

    # --------------------------------------------------------
    # Create browser workers
    # --------------------------------------------------------

    drivers = []

    print(
        "[1/3] Starting Selenium workers..."
    )

    try:

        for _ in range(
            min(
                CONCURRENT_TABS,
                len(pending),
            )
        ):

            driver = create_driver(
                OUTPUT_DIR
            )

            drivers.append(driver)

        print(
            f"Started {len(drivers)} Chrome workers."
        )

        print()

        # ----------------------------------------------------
        # Queue
        # ----------------------------------------------------

        queue_index = 0

        completed = 0

        failed = []

        progress = tqdm(
            total=len(pending),
            desc="Downloading",
            unit="pdf",
            dynamic_ncols=True,
        )

        # ----------------------------------------------------
        # Each worker gets a job, finishes it, then gets
        # another job.
        # ----------------------------------------------------

        worker_jobs = {}

        for driver in drivers:

            if queue_index >= len(
                pending
            ):
                break

            worker_jobs[driver] = (
                pending[queue_index],
                1,
            )

            queue_index += 1

        # ----------------------------------------------------
        # Process jobs.
        #
        # This is intentionally sequential per browser worker.
        # Three Selenium browsers operate independently.
        # ----------------------------------------------------

        while worker_jobs:

            for driver, job in list(
                worker_jobs.items()
            ):

                row, attempt = job

                success, result = download_one(
                    driver,
                    row,
                    OUTPUT_DIR,
                )

                # --------------------------------------------
                # Success
                # --------------------------------------------

                if success:

                    completed += 1

                    progress.update(1)

                    # Assign next job.
                    if queue_index < len(
                        pending
                    ):

                        worker_jobs[
                            driver
                        ] = (
                            pending[
                                queue_index
                            ],
                            1,
                        )

                        queue_index += 1

                    else:

                        del worker_jobs[
                            driver
                        ]

                    continue

                # --------------------------------------------
                # Retry
                # --------------------------------------------

                if attempt < MAX_RETRIES:

                    worker_jobs[
                        driver
                    ] = (
                        row,
                        attempt + 1,
                    )

                    # Small backoff.
                    time.sleep(
                        min(
                            2 ** attempt,
                            8,
                        )
                    )

                    continue

                # --------------------------------------------
                # Permanent failure
                # --------------------------------------------

                failed.append(
                    {
                        "row": row,
                        "error": result,
                    }
                )

                progress.update(1)

                # Next job.
                if queue_index < len(
                    pending
                ):

                    worker_jobs[
                        driver
                    ] = (
                        pending[
                            queue_index
                        ],
                        1,
                    )

                    queue_index += 1

                else:

                    del worker_jobs[
                        driver
                    ]

        progress.close()

    except KeyboardInterrupt:

        print()
        print(
            "Interrupted by user."
        )

        print(
            "Already completed PDFs "
            "will be skipped on the next run."
        )

    finally:

        print()
        print(
            "[3/3] Closing Selenium..."
        )

        for driver in drivers:

            try:
                driver.quit()
            except Exception:
                pass

    # --------------------------------------------------------
    # Save failures
    # --------------------------------------------------------

    if failed:

        with open(
            FAILED_FILE,
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                [
                    "Case Subject",
                    "Case No",
                    "Case Title",
                    "Download",
                    "Error",
                ]
            )

            for item in failed:

                row = item["row"]

                writer.writerow(
                    [
                        row.get(
                            "Case Subject",
                            "",
                        ),
                        row.get(
                            "Case No",
                            "",
                        ),
                        row.get(
                            "Case Title",
                            "",
                        ),
                        row.get(
                            "Download",
                            "",
                        ),
                        item["error"],
                    ]
                )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print(" COMPLETE")
    print("=" * 72)

    print(
        f"Downloaded : {completed}"
    )

    print(
        f"Previously : {skipped}"
    )

    print(
        f"Failed     : {len(failed)}"
    )

    print(
        f"Total      : {len(rows)}"
    )

    print()
    print(
        f"PDF folder : {OUTPUT_DIR}"
    )

    if failed:

        print(
            f"Failures   : {FAILED_FILE}"
        )

    print()


if __name__ == "__main__":
    main()