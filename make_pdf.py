import os
from fpdf import FPDF

# Paths (absolute)
MD_PATH = r"D:\Descargas\rsi_macd_divergence\explanation.md"
PDF_PATH = r"D:\Descargas\rsi_macd_divergence\explanation.pdf"

# Read markdown lines
with open(MD_PATH, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Helvetica", size=12)

for line in lines:
    if line.startswith("#"):
        # Header: bigger bold font
        pdf.set_font("Helvetica", style="B", size=16)
        txt = line.lstrip("# ")
        clean = txt.encode('latin-1', errors='ignore').decode('latin-1')
        pdf.cell(0, 10, txt=clean, ln=1)
        pdf.set_font("Helvetica", size=12)
    else:
        # Normal paragraph (multi-cell handles wrapping)
        clean_line = line.encode('latin-1', errors='ignore').decode('latin-1')
        pdf.cell(0, 7, txt=clean_line, ln=1)

pdf.output(PDF_PATH)
print(f"PDF written to {PDF_PATH}")
