#!/usr/bin/env python3
import json
import os
import sys
import re

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_site():
    print("Running automated site verification checks...")
    errors = []

    # Check surprises.json manifest
    manifest_path = "surprises.json"
    if not os.path.exists(manifest_path):
        errors.append("surprises.json manifest missing!")
    else:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifest = data.get("manifest", [])
            if len(manifest) != 20:
                errors.append(f"Manifest entry count mismatch! Expected 20, got {len(manifest)}")
            expected = [f"{i:02d}" for i in range(1, 21)]
            actual = [entry.get("sticker_number") for entry in manifest]
            if actual != expected:
                errors.append("Manifest sticker numbers must be exactly 01 through 20 in order")
            for entry in manifest:
                if entry.get("implementation_status") != "verified":
                    errors.append(f"Surprise {entry.get('sticker_number')} not verified against approved content")
        except Exception as e:
            errors.append(f"Invalid surprises.json format: {e}")

    # Check all 20 surprise destinations
    for i in range(1, 21):
        num_str = f"{i:02d}"
        page_path = f"surprises/{num_str}/index.html"
        if not os.path.exists(page_path):
            errors.append(f"Missing page: {page_path}")
        else:
            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Check for prohibited nicknames
                if re.search(r'\b(tinkerbell|tink)\b', content, re.I):
                    errors.append(f"Prohibited nickname found in {page_path}")

    # Check root index.html and assets
    if not os.path.exists("index.html"):
        errors.append("Root index.html missing!")
    if not os.path.exists("assets/css/style.css"):
        errors.append("assets/css/style.css missing!")

    # Check USDZ AR models
    for model in ["iloveyou.usdz", "heart.usdz", "ufo.usdz"]:
        m_path = f"assets/models/{model}"
        if not os.path.exists(m_path):
            errors.append(f"AR asset missing: {m_path}")

    if errors:
        print("\n❌ SITE VERIFICATION FAILED:")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\n✅ MANIFEST, CONTENT GATES AND SITE STRUCTURE PASSED!")

if __name__ == "__main__":
    test_site()
