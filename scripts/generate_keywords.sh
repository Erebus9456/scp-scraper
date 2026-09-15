#!/usr/bin/env bash
set -e

# Dynamically resolve project root directory (one level up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OUTPUT_FILE="$PROJECT_ROOT/data/input/keywords.csv"

# Ensure data/input directory exists in the project root
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Write header
echo "keyword" > "$OUTPUT_FILE"

# Append lowercase letters a through z (one per line)
for char in {a..z}; do
    echo "$char" >> "$OUTPUT_FILE"
done

echo "[✓] Successfully generated '$OUTPUT_FILE' with keywords (a-z)."