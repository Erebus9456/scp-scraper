#!/usr/bin/env bash
set -e

echo "=================================================="
echo "         SCP Scraper Environment Setup             "
echo "=================================================="

# 1. Ensure Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not available in PATH."
    exit 1
fi

# 2. Check for or create .venv
if [ ! -d ".venv" ]; then
    echo "[*] Virtual environment (.venv) not found. Creating one..."
    python3 -m venv .venv
    echo "[✓] .venv created successfully."
else
    echo "[*] Existing .venv found."
fi

# 3. Upgrade pip inside .venv
echo "[*] Upgrading pip..."
.venv/bin/pip install --upgrade pip --quiet

# 4. Install required packages
echo "[*] Installing requirements (Selenium & Webdriver Manager)..."
.venv/bin/pip install -r requirements.txt

# 5. Ensure execution permissions for scripts
chmod +x setup.sh 2>/dev/null || true
chmod +x start.sh 2>/dev/null || true

echo ""
echo "=================================================="
echo "  Setup Complete!                                 "
echo "  Run your scraper anytime using: ./start.sh      "
echo "=================================================="