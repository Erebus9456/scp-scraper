# Supreme Court Pakistan Scraper ⚖️

A Python + Selenium automation project for searching the Supreme Court of Pakistan judgment portal, extracting result rows, handling CAPTCHA protection gracefully, de-duplicating findings across keywords, and downloading judgment PDFs reliably.

This project was built to work against a real ASP.NET WebForms portal that uses bot protection, dynamic table rendering, and Akamai-protected PDF delivery. The implementation is designed to be resilient rather than brittle.

---

## Project Purpose

The scraper does the following:

- reads keyword input from a CSV file
- searches the Supreme Court judgment portal for each keyword
- waits for and handles CAPTCHA or anti-bot challenges through a human-assisted flow
- synchronizes with ASP.NET postbacks and partial page refreshes
- navigates dynamic pagination and result groups
- extracts metadata from judgment rows
- tracks duplicate cases across keywords
- downloads PDF judgment files and saves them into a structured output folder
- writes CSV data and failed-download logs for traceability

---

## Project-wide Specs

### 1. Core Stack

- Python 3
- Selenium WebDriver
- Google Chrome / Chromium
- webdriver-manager
- CSV-based storage
- Optional progress output with tqdm
- Human-in-the-loop CAPTCHA handling

### 2. Execution Model

The project is intentionally browser-driven rather than pure HTTP-based scraping:

- many court portals require a live browser context to establish session state
- CAPTCHA and anti-bot layers often reject non-browser requests
- ASP.NET pages rely heavily on view state, event validation, and asynchronous postbacks
- Chrome automation is used to preserve a realistic browsing session while still allowing deterministic control

### 3. Search and Extraction Workflow

The scraper follows a multi-stage workflow:

1. Load keywords from data/input/keywords.csv
2. Open the search portal
3. Enter one keyword at a time
4. Submit form and wait for results
5. Detect zero-result states, CAPTCHA state, and page reloads
6. Parse result rows from the GridView table
7. Extract fields such as case number, case title, judge, date, citation, and PDF link
8. Continue across paginated result groups
9. Save data to CSV outputs
10. De-duplicate rows by case number across keyword searches
11. Download PDFs for each judgment row via Selenium-controlled browser download behavior

### 4. Data Outputs

The project creates structured artifacts under data/:

- input keywords file
- output result CSVs
- duplicate case CSV
- downloaded judgment PDFs
- failed download log if any PDF fetch fails

### 5. Stability Requirements

The scraper is built around a few operational assumptions:

- the target site may block or delay requests under load
- page state can change after postback
- pagination can use disguised or dynamic links
- CAPTCHA may appear unexpectedly
- the PDF endpoint may behave differently from normal HTTP downloads because of Akamai protection

The tool is therefore tolerant of timeouts, retries, and manual interventions.

---

## Difficulties and Solutions

### Difficulty 1: ASP.NET WebForms postback behavior

The portal is built on ASP.NET WebForms, which heavily depends on hidden form state, event delegation, and asynchronous page updates.

The project solves this by:

- using explicit waits for page load and element visibility
- re-checking the DOM before reading results
- waiting after form submission to allow postback stabilization
- targeted XPath selectors for the specific GridView and search controls
- avoiding assumptions that the page is stable immediately after a click

### Difficulty 2: Dynamic result tables and pagination

The results are not always straightforward static HTML. Some pages use:

- hidden panels
- grid row groups
- pagination links with ASP.NET-generated URLs
- ellipsis or grouped page navigation

The solution includes:

- grid-level table detection
- row extraction based on CSS/XPath patterns
- pagination logic that follows the actual portal's link structure
- safe fallback when no rows are present

### Difficulty 3: CAPTCHA / bot protection

The portal uses CAPTCHA-based anti-bot protection. A HEADLESS or overly automated browser can easily trigger the bot filter.

The graceful solution is a human-in-the-loop flow:

- the script pauses when a CAPTCHA challenge appears
- the user is prompted to solve it manually in the visible browser
- once the CAPTCHA is solved and the page returns to a normal state, the scraper resumes automatically
- no hard crash occurs; the script waits for the page to recover instead of failing immediately

This makes the scraper resilient to protection layers without forcing a brittle automation-only workaround.

### Difficulty 4: Duplicate judgment records across keywords

The same judgment may be returned for multiple search keywords, and the portal does not guarantee unique rows per keyword.

The project addresses this by:

- normalizing case numbers and titles
- storing results per keyword
- de-duplicating records using case identifiers when possible
- writing a separate duplicate CSV with case numbers and keyword presence

### Difficulty 5: PDF download protection by Akamai

This was one of the most important technical blockers.

The Supreme Court of Pakistan’s PDF server is behind Akamai, and direct downloads through requests, curl, and other raw HTTP methods fail with 403 errors. A direct HTTP fetch is not a reliable solution because the server treats it as a bot or blocked client.

The working solution used Selenium and a real browser session:

- Selenium opens the PDF in a genuine Chrome session
- Chrome is allowed to process the PDF request as a normal browser request
- the browser session avoids the Akamai bot blocks that raw HTTP clients hit

### Difficulty 6: Chrome opening PDFs in its built-in viewer

Even after Selenium could access the PDF URL, Chrome initially opened the PDF inside the built-in PDF viewer instead of actually saving it to disk.

This was solved by:

- disabling the Chrome PDF extension
- setting the browser preference to open PDFs externally
- using Chrome download behavior via the DevTools Protocol
- configuring a real download directory and allowing downloads in headless mode

This is the key configuration that changed the behavior from “view in browser” to “save as real PDF file.”

### Difficulty 7: Validating file integrity

Some downloads may be corrupted, empty, or incomplete due to blocked responses or partial writes.

The project validates each downloaded file by:

- checking that it exists
- checking minimum file size
- validating the first bytes match the PDF magic header %PDF
- re-attempting failed downloads with a retry policy

### Difficulty 8: Concurrency and reliability

Multiple browser workers can download in parallel, but too much concurrency can trigger protection and destabilize the portal.

The project therefore uses a conservative browser pool and a retry loop, balancing throughput with reliability.

---

## Graceful reCAPTCHA Solution

The project is intentionally designed around a graceful anti-bot workflow rather than a forced break.

### Behavior

When the portal presents a CAPTCHA or anti-bot challenge:

- the scraper pauses the automation flow
- a visible Chrome window remains available for the user
- the user solves the challenge manually
- the script waits for the page to return to a usable state
- the next action continues automatically

### Why this is important

A fully automated bot bypass is unstable and fragile on a protected judicial portal. Human-assisted verification is much more reliable because it respects the site’s real security model while preserving the scraping workflow.

In short, the scraper does not treat CAPTCHA as a hard failure. It treats it as a normal operational gate that can be resolved by human intervention without losing progress.

---

## PDF Download Fix (Akamai + Chrome)

The final workable fix for PDF delivery was:

- avoid requests/curl direct fetches because Akamai rejects them with 403
- use Selenium with a real Chrome browser session
- disable Chrome’s PDF extension
- set Chrome to download PDFs externally instead of displaying them inline
- set the browser’s download directory and allow the download behavior through CDP
- validate the saved file is a true PDF before accepting it

The actual project implementation does this in the download workflow:

- `--disable-pdf-extension`
- `plugins.always_open_pdf_externally = True`
- `Page.setDownloadBehavior` with allow and a target download path
- PDF file validation using file size and `%PDF` header check

This combination allows the script to save the actual PDFs reliably even when the source server is behind Akamai protection.

---

## Directory Structure

```text
.
├── data/
│   ├── input/
│   │   └── keywords.csv
│   ├── judgements_pdf/
│   │   └── downloaded_pdf_files_here
│   └── output/
│       ├── duplicate_judgments.csv
│       ├── judgments_results.csv
│       ├── judgments_results_A_M.csv
│       ├── judgments_results_N_T.csv
│       ├── judgments_results_U_Z.csv
│       ├── tax_judgements.csv
│       └── unique_judgements.csv
├── logs/
├── scripts/
│   ├── download_judgements.py
│   ├── generate_keywords.sh
│   ├── merge_results.py
│   ├── setup.sh
│   ├── start.sh
│   └── numpy_scripts/
│       ├── tax_judgements.py
│       └── unique_judgements.py
├── src/
│   ├── __init__.py
│   ├── browser.py
│   ├── config.py
│   ├── extractor.py
│   ├── paginator.py
│   ├── search_flow.py
│   └── storage.py
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Core Files

- main.py: entry point for the project workflow
- src/config.py: selectors, portals, file paths, and timing constants
- src/browser.py: browser startup and Chrome configuration
- src/search_flow.py: form submission, CAPTCHA handling, and search flow logic
- src/extractor.py: result parsing and metadata extraction
- src/paginator.py: ASP.NET pagination handling
- src/storage.py: CSV output and duplicate logic
- scripts/download_judgements.py: direct Selenium-based PDF downloader for court judgments

---

## Execution Notes

- Many parts of the scraper are intentionally modular to support debugging and non-trivial court-portal behavior.
- The portal can reject automated traffic; a visible Chrome session and manual CAPTCHA resolution are part of the intended operating model.
- When a PDF fails to download, the script records it in a failure log and retries with a bounded retry policy.

---

## Summary

This project is a browser-automation scraper for a protected legal database. It handles tedious court-site mechanics, anti-bot protections, dynamic pagination, PDF delivery restrictions, and duplicate judgment detection in a practical and resilient way.

The most significant technical lessons are:

- direct HTTP access is not enough for Akamai-protected PDFs
- real browser sessions are required for this portal
- Chrome PDF viewer behavior must be disabled to preserve file downloads
- CAPTCHA should be handled gracefully, not treated as a fatal system error

This gives the project a reliable operational path even in the presence of difficult anti-bot and PDF-delivery protections.