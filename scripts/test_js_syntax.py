#!/usr/bin/env python3
"""
Validates JavaScript syntax across all 20 surprise pages using node --check.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent

def check_all_js():
    print("Checking JavaScript syntax across all 20 surprise experiences...")
    pages = sorted((ROOT / "surprises").glob("*/index.html"))
    if len(pages) != 20:
        print(f"Error: Found {len(pages)} surprise pages instead of 20!")
        sys.exit(1)

    errors = 0
    total_scripts = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.S | re.I)
            surprise_num = page.parent.name
            for index, script in enumerate(scripts):
                script_text = script.strip()
                if not script_text:
                    continue
                total_scripts += 1
                target = tmp_path / f"surprise-{surprise_num}-{index}.js"
                target.write_text(script_text, encoding="utf-8")
                res = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True)
                if res.returncode != 0:
                    print(f"[FAIL] Syntax error in surprise #{surprise_num} script {index}:")
                    print(res.stderr)
                    errors += 1
                else:
                    print(f"  [OK] Surprise #{surprise_num} script syntax OK")

    if errors == 0:
        print(f"\n[PASS] All {total_scripts} JavaScript scripts passed node --check with 0 syntax errors.")
    else:
        print(f"\n[FAIL] Encountered {errors} syntax errors in JavaScript checks.")
        sys.exit(1)

if __name__ == "__main__":
    check_all_js()
