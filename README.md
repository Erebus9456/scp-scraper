# ⚖️ Supreme Court Pakistan Scraper

> **A resilient browser-automation pipeline for extracting, deduplicating, and downloading Supreme Court of Pakistan judgments from a protected ASP.NET WebForms portal.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?style=for-the-badge&logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Chrome](https://img.shields.io/badge/Chrome-WebDriver-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)](https://www.google.com/chrome/)
[![CSV](https://img.shields.io/badge/Storage-CSV-orange?style=for-the-badge)]

---

## 🧭 Overview

The **Supreme Court Pakistan Scraper** is a Python + Selenium automation system built to work against a real-world judicial portal with:

- ASP.NET WebForms
- Dynamic GridView result tables
- Server-side postbacks
- Partial page updates
- CAPTCHA / anti-bot protection
- Dynamic pagination
- Akamai-protected PDF endpoints
- Browser-only download behavior

Rather than relying on fragile HTTP requests or static HTML parsing, the system operates through a **real Chrome browser session**, allowing it to reproduce the interaction model expected by the portal.

The result is a scraper designed around **resilience, recoverability, and traceability**.

---

# 🚀 What It Does

```text
                    KEYWORDS
                       │
                       ▼
              ┌─────────────────┐
              │  Search Portal  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ CAPTCHA / Bot   │
              │ Human-assisted  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Result GridView │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Metadata        │
              │ Extraction      │
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Pagination         Deduplication
              │                 │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Judgment PDFs   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Validation      │
              │ + Retry         │
              └────────┬────────┘
                       ▼
                 Structured Data
```

---

# ✨ Key Capabilities

### 🔎 Keyword-driven search

Reads keywords from:

```text
data/input/keywords.csv
```

and systematically searches the judicial portal for each term.

### 🧠 Intelligent result extraction

Extracts structured judgment metadata including:

- Case Subject
- Case Number
- Case Title
- Author Judge
- Judgment Date
- Upload Date
- Citation
- Supreme Court Citation
- PDF download URL
- Search keyword

### 📄 Reliable PDF acquisition

Downloads actual judgment PDFs using Selenium-controlled Chrome rather than relying on direct HTTP requests.

### ♻️ Duplicate detection

The same judgment can appear under multiple search terms.

The pipeline identifies duplicate cases and maintains dedicated duplicate output data.

### 🛡️ CAPTCHA-aware execution

CAPTCHA is treated as an **operational checkpoint**, not a fatal error.

The browser remains available for manual verification and automatically resumes once the portal returns to a usable state.

### 📊 Traceable outputs

Every stage produces structured artifacts, allowing results and failures to be inspected independently.

---

# 🧩 Why Browser Automation?

A conventional scraper might attempt:

```text
requests
   ↓
HTML
   ↓
BeautifulSoup
   ↓
Data
```

That approach is unreliable for this portal.

The actual environment behaves more like:

```text
Chrome
  │
  ├── Session / Cookies
  ├── ASP.NET ViewState
  ├── EventValidation
  ├── JavaScript
  ├── Partial Postbacks
  ├── CAPTCHA State
  └── Akamai Session
          │
          ▼
       Portal
```

The scraper therefore intentionally uses a **real browser context**.

This preserves the state required by the application and makes the automation significantly more robust against the portal's dynamic behavior.

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────┐
│                main.py                   │
│             Application Flow             │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│              search_flow.py              │
│ Search • Submit • CAPTCHA • Recovery     │
└────────────────────┬─────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│    browser.py    │   │   paginator.py   │
│ Chrome / Selenium│   │ ASP.NET Pages   │
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
          ┌──────────────────┐
          │   extractor.py   │
          │ Metadata Parsing  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │    storage.py    │
          │ CSV + Dedup      │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ PDF Downloader   │
          │ Selenium + CDP   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ PDF Validation   │
          │ Retry + Logging  │
          └──────────────────┘
```

---

# 🧰 Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| Browser Automation | Selenium WebDriver |
| Browser | Google Chrome / Chromium |
| Driver Management | webdriver-manager |
| Data Storage | CSV |
| Progress Reporting | tqdm |
| Browser Protocol | Chrome DevTools Protocol |
| Target Architecture | ASP.NET WebForms |
| PDF Delivery | Selenium-controlled Chrome |
| Anti-Bot Handling | Human-in-the-loop CAPTCHA |

---

# 🔐 The Hard Parts

This isn't a scraper built against a clean REST API.

Several aspects of the target system required dedicated engineering.

---

## 1. ASP.NET WebForms

The portal relies heavily on the ASP.NET WebForms lifecycle.

That means requests can depend on:

- `__VIEWSTATE`
- `__EVENTVALIDATION`
- server-side events
- generated control IDs
- asynchronous postbacks
- dynamically rendered elements

Instead of trying to reconstruct those requests manually, the scraper allows Chrome to execute the application's normal browser workflow.

### Result

```text
User-like interaction
        ↓
ASP.NET lifecycle
        ↓
Stable browser state
        ↓
Extractable DOM
```

---

# 2. Dynamic Result Tables

Judgment results are rendered through an ASP.NET GridView-style structure.

The scraper therefore avoids assumptions such as:

> "The results will always exist immediately after clicking Search."

Instead it:

1. Submits the search.
2. Waits for the page state to stabilize.
3. Detects the result grid.
4. Extracts available rows.
5. Determines pagination state.
6. Moves through subsequent result groups.
7. Re-validates the DOM after navigation.

This makes the extraction layer considerably less sensitive to timing differences.

---

# 3. CAPTCHA & Anti-Bot Protection

The portal may introduce CAPTCHA or other anti-automation challenges.

The project intentionally uses a **human-assisted recovery model**.

```text
             Search
                │
                ▼
        ┌───────────────┐
        │ CAPTCHA found?│
        └───────┬───────┘
                │
        ┌───────┴───────┐
        │               │
       NO              YES
        │               │
        ▼               ▼
    Continue       Pause automation
                        │
                        ▼
                 Human solves CAPTCHA
                        │
                        ▼
                 Detect recovery
                        │
                        ▼
                     Resume
```

The scraper does not treat CAPTCHA as an unrecoverable exception.

Instead:

> **CAPTCHA becomes a temporary human verification checkpoint inside an otherwise automated pipeline.**

This is considerably more practical than attempting to make the entire workflow blindly autonomous against a protected judicial portal.

---

# 4. Duplicate Judgments

A judgment may be returned for several different keywords.

For example:

```text
Keyword A
    └── C.P. 123/2020

Keyword B
    └── C.P. 123/2020

Keyword C
    └── C.P. 123/2020
```

Without deduplication, this produces multiple records for the same judgment.

The pipeline therefore maintains:

```text
Raw Results
     │
     ▼
Normalize identifiers
     │
     ▼
Detect duplicate cases
     │
     ├── Unique judgments
     │
     └── Duplicate judgments
```

Case numbers are used as the primary identity signal where available, with additional metadata available for normalization and analysis.

---

# 📥 5. The PDF Problem

The most challenging component was not extracting the search results.

It was downloading the actual judgment PDFs.

The PDF endpoint is protected by **Akamai**, meaning direct HTTP approaches such as:

```text
requests
curl
wget
```

can receive:

```text
HTTP 403 Forbidden
```

even when the same URL works perfectly inside Chrome.

This creates an important distinction:

```text
HTTP Client
     │
     ▼
Akamai
     │
     ✕
    403


Chrome Browser
     │
     ▼
Akamai
     │
     ▼
    PDF
```

The solution was to perform the download through the **same browser environment that successfully accesses the portal**.

---

# 🛠️ 6. Turning Chrome's PDF Viewer into a Downloader

Even after Selenium could access the PDF, Chrome initially displayed it inside its built-in PDF viewer.

That meant:

```text
PDF URL
   ↓
Chrome
   ↓
PDF Viewer
   ↓
Nothing saved
```

The final implementation configures Chrome to behave as a download client instead:

```text
PDF URL
   ↓
Chrome
   ↓
External PDF handling
   ↓
Download directory
   ↓
Actual .pdf file
```

The browser is configured using:

```text
--disable-pdf-extension
```

and:

```text
plugins.always_open_pdf_externally = true
```

The project additionally configures Chrome's download behavior through the **Chrome DevTools Protocol**.

---

# ✅ 7. PDF Integrity Validation

A successful browser navigation does not necessarily mean a valid PDF was saved.

Every download therefore goes through validation.

```text
Download
   │
   ▼
File exists?
   │
   ▼
Minimum size?
   │
   ▼
PDF magic header?
   │
   ▼
%PDF
   │
   ▼
VALID
```

The implementation checks the PDF signature:

```text
%PDF
```

This helps detect:

- empty files
- partial downloads
- HTML error pages
- blocked responses
- corrupted output

Failed downloads can then enter the retry workflow.

---

# 🔁 Retry & Recovery

The scraper is designed around the assumption that network automation will occasionally fail.

Instead of:

```text
Error → Crash
```

the workflow follows:

```text
Error
  │
  ▼
Classify
  │
  ├── Temporary → Retry
  ├── CAPTCHA  → Human intervention
  ├── Timeout  → Wait + retry
  └── Invalid PDF → Redownload
```

This makes long-running scraping jobs significantly easier to recover.

---

# 📂 Project Structure

```text
.
├── data/
│   ├── input/
│   │   └── keywords.csv
│   │
│   ├── judgements_pdf/
│   │   └── downloaded_judgments/
│   │
│   └── output/
│       ├── duplicate_judgments.csv
│       ├── judgments_results.csv
│       ├── judgments_results_A_M.csv
│       ├── judgments_results_N_T.csv
│       ├── judgments_results_U_Z.csv
│       ├── tax_judgements.csv
│       └── unique_judgements.csv
│
├── logs/
│
├── scripts/
│   ├── download_judgements.py
│   ├── generate_keywords.sh
│   ├── merge_results.py
│   ├── setup.sh
│   ├── start.sh
│   │
│   └── numpy_scripts/
│       ├── tax_judgements.py
│       └── unique_judgements.py
│
├── src/
│   ├── __init__.py
│   ├── browser.py
│   ├── config.py
│   ├── extractor.py
│   ├── paginator.py
│   ├── search_flow.py
│   └── storage.py
│
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 🧩 Core Components

### `main.py`

Application entry point and orchestration layer.

### `src/browser.py`

Responsible for:

- Chrome initialization
- Selenium configuration
- download preferences
- browser session management

### `src/config.py`

Central configuration for:

- selectors
- URLs
- paths
- timeouts
- retry parameters

### `src/search_flow.py`

Controls:

- keyword submission
- search lifecycle
- CAPTCHA detection
- recovery
- result-state detection

### `src/extractor.py`

Extracts judgment metadata from the result grid.

### `src/paginator.py`

Handles the portal's ASP.NET pagination model.

### `src/storage.py`

Responsible for:

- CSV persistence
- normalization
- duplicate detection
- result organization

### `scripts/download_judgements.py`

Dedicated Selenium PDF downloader responsible for:

- browser-based PDF access
- Chrome download configuration
- retry handling
- file validation
- download logging

---

# 📊 Output Data

The primary result schema contains:

| Field | Description |
|---|---|
| `Keyword` | Search term that produced the result |
| `Case Subject` | Subject/category of the case |
| `Case No` | Case identifier |
| `Case Title` | Full case title |
| `Author Judge` | Authoring judge |
| `Judgment Date` | Date of judgment |
| `Upload Date` | Portal upload date |
| `Citation` | Report citation |
| `SC Citation` | Supreme Court citation |
| `Download` | Judgment PDF URL |

---

# 🔬 Data Pipeline

```text
keywords.csv
     │
     ▼
Keyword Search
     │
     ▼
Raw Results
     │
     ├───────────────┐
     ▼               ▼
Metadata          PDF URLs
Extraction            │
     │                ▼
     ▼            Browser Download
Deduplication          │
     │                ▼
     ▼            PDF Validation
CSV Output             │
                      ▼
                 Local Archive
```

---

# ⚙️ Execution

Install dependencies:

```bash
pip install -r requirements.txt
```

Prepare your keyword file:

```text
data/input/keywords.csv
```

Then run the scraper:

```bash
python main.py
```

For the dedicated PDF download workflow:

```bash
python scripts/download_judgements.py
```

---

# 🧪 Operational Philosophy

This project is built around a few principles:

### Don't fight the browser

If the website requires a browser, use a browser.

### Don't assume the DOM is static

Wait for the application state you actually need.

### Don't treat CAPTCHA as a crash

Pause, allow human verification, then resume.

### Don't trust a download blindly

Validate the resulting file.

### Don't sacrifice reliability for concurrency

A slightly slower scraper that survives thousands of records is more useful than a fast scraper that gets blocked halfway through.

---

# ⚖️ Scope & Responsible Use

This project is intended for legitimate research, indexing, analysis, and archival workflows involving publicly accessible judicial information.

The CAPTCHA workflow is intentionally **human-in-the-loop** rather than attempting to bypass or defeat the site's verification mechanism.

Users should operate the scraper responsibly and respect the target site's terms, access policies, rate limits, and applicable laws.

---

# 🧠 Engineering Takeaways

The project demonstrates several practical lessons from automating a production-like protected web application:

> **Browser automation is sometimes more reliable than HTTP scraping.**

> **ASP.NET WebForms requires synchronization with application state, not just HTML parsing.**

> **A successful navigation is not the same thing as a successful file download.**

> **Protected PDF endpoints may behave completely differently from the pages that link to them.**

> **Resilient automation needs recovery paths, not just happy paths.**

---

# 🏁 Result

What started as a simple keyword scraper evolved into a complete legal-data extraction pipeline capable of handling:

```text
                    ┌──────────────┐
                    │   Keywords   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ WebForms     │
                    │ Search       │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ CAPTCHA      │
                    │ Recovery     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Pagination   │
                    │ + Extraction │
                    └──────┬───────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          ┌──────────────┐    ┌──────────────┐
          │ Deduplication│    │ PDF Download │
          └──────┬───────┘    └──────┬───────┘
                 │                   │
                 │            ┌──────▼───────┐
                 │            │ PDF Validate │
                 │            └──────┬───────┘
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    ┌──────────────┐
                    │ Structured   │
                    │ Legal Data   │
                    └──────────────┘
```

**A scraper that doesn't just extract data — it survives the system it's extracting it from.** ⚖️