#!/bin/bash
# PDF to PPTX Converter — wrapper script
# Usage:
#   ./convert_pdf.sh input.pdf                     → creates input.pptx
#   ./convert_pdf.sh input.pdf -o output.pptx      → custom output name
#   ./convert_pdf.sh input.pdf --dpi 300            → higher quality

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/converter_venv/bin/activate"
python3 "$SCRIPT_DIR/pdf_to_pptx.py" "$@"
