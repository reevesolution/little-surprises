#!/usr/bin/env python3
import json
import os
import sys

def generate_printable_sticker_sheet(base_url="https://username.github.io/little-surprises/"):
    """
    Generates a printable HTML sticker sheet formatted for Letter size paper (8.5 x 11 inches).
    4 columns x 5 rows grid (20 stickers total).
    Each QR sticker contains a ~1.5 inch square QR code and sticker number (01-20). No descriptions on stickers.
    """
    if not base_url.endswith('/'):
        base_url += '/'

    with open("surprises.json", "r") as f:
        data = json.load(f)

    manifest = data.get("manifest", [])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Printable QR Sticker Sheet (4x5 Grid - 20 Stickers)</title>
  <style>
    @page {{
      size: letter portrait;
      margin: 0.4in;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #FFFFFF;
      color: #000000;
      width: 8.5in;
      height: 11in;
      margin: 0 auto;
      padding: 0.4in;
    }}
    .no-print-banner {{
      background: #FFFBEB;
      border: 1px solid #F59E0B;
      color: #92400E;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 20px;
      font-size: 0.9rem;
    }}
    @media print {{
      .no-print-banner {{
        display: none;
      }}
      body {{
        padding: 0;
      }}
    }}
    .sticker-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1.75in);
      grid-template-rows: repeat(5, 1.9in);
      gap: 0.15in 0.2in;
      justify-content: center;
      align-content: center;
    }}
    .sticker {{
      width: 1.75in;
      height: 1.9in;
      border: 1px dashed #CBD5E1;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 0.08in;
      background: #FFFFFF;
      page-break-inside: avoid;
    }}
    .qr-container {{
      width: 1.4in;
      height: 1.4in;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #FFFFFF;
      padding: 4px; /* Quiet zone around QR code */
    }}
    .qr-container img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .sticker-number {{
      font-size: 0.85rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: #1E293B;
      margin-top: 2px;
    }}
  </style>
</head>
<body>

  <div class="no-print-banner">
    <strong>🖨️ Printable Sticker Sheet Instructions:</strong><br>
    Target Base URL: <code>{base_url}</code><br>
    • Letter Size (8.5" x 11") | 4 Columns x 5 Rows Grid (20 Stickers)<br>
    • Press <code>Ctrl+P</code> or <code>Cmd+P</code> to print. Ensure margin is set to 'None' or 'Default'.
  </div>

  <div class="sticker-grid">
"""

    for item in manifest:
        num = item["sticker_number"]
        route = item["route"]
        target_url = f"{base_url}{route}"
        # QuickChart QR API generates clean vector-style QR codes with proper quiet zones
        qr_api_url = f"https://quickchart.io/qr?text={target_url}&size=200&margin=2"

        html_content += f"""    <div class="sticker">
      <div class="qr-container">
        <img src="{qr_api_url}" alt="QR {num}">
      </div>
      <div class="sticker-number">#{num}</div>
    </div>
"""

    html_content += """  </div>

</body>
</html>
"""

    output_file = "sticker_sheet.html"
    with open(output_file, "w") as f:
        f.write(html_content)
    print(f"Printable sticker sheet successfully generated: {output_file}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://username.github.io/little-surprises/"
    generate_printable_sticker_sheet(url)
