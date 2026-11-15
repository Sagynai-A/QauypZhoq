#!/usr/bin/env python3
"""Download the current PhishTank online-valid database into phishtank.txt.

The website's index.html loads phishtank.txt from the same directory at startup.
Run manually with: python update_phishtank.py [APP_KEY]
Or set PHISHTANK_APP_KEY in the environment.
"""

import bz2
import csv
import io
import os
import sys
import tempfile
import urllib.request
from pathlib import Path


def main() -> int:
    key = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("PHISHTANK_APP_KEY", "")).strip()
    key_path = f"{key}/" if key else ""
    url = f"http://data.phishtank.com/data/{key_path}online-valid.csv.bz2"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "phishtank/qauypzhoq",
            "Accept": "application/octet-stream",
        },
    )

    print("Downloading the PhishTank database...")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            compressed = response.read()
        csv_text = bz2.decompress(compressed).decode("utf-8-sig", "replace")
    except Exception as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1

    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames or "url" not in reader.fieldnames:
        print("Unexpected PhishTank CSV format: 'url' column not found.", file=sys.stderr)
        return 1

    urls = sorted({(row.get("url") or "").strip() for row in reader if (row.get("url") or "").strip()})
    if not urls:
        print("The downloaded database is empty; existing phishtank.txt was not changed.", file=sys.stderr)
        return 1

    output = Path(__file__).resolve().parent / "phishtank.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents the website from seeing a partially written file.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=output.parent, delete=False) as tmp:
        tmp.write("\n".join(urls) + "\n")
        temp_name = tmp.name
    os.replace(temp_name, output)

    print(f"Done: {len(urls):,} unique phishing URLs saved to {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
