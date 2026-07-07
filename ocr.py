"""
ocr.py
======
Handwriting / text extraction for GestureCanvas, powered by Tesseract via
pytesseract. Triggered with the Space key while the app is running.

If the Tesseract binary isn't installed on the host machine, this module
degrades gracefully and reports exactly what's missing rather than
crashing the whole application.
"""

import shutil

import config

try:
    import pytesseract
    if config.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    OCR_AVAILABLE = bool(shutil.which("tesseract") or config.TESSERACT_CMD)
except ImportError:
    pytesseract = None
    OCR_AVAILABLE = False


def extract_text(canvas):
    """
    Run OCR against the canvas's current drawing.
    Returns (success: bool, message: str).
    """
    if not OCR_AVAILABLE:
        return False, (
            "Tesseract OCR engine not found. Install it and make sure it's on "
            "your PATH (e.g. `sudo apt install tesseract-ocr` on Linux, or "
            "download the installer on Windows and set TESSERACT_CMD in config.py)."
        )

    if not canvas.has_ink():
        return False, "Nothing to read yet -- draw something first."

    try:
        ocr_ready_image = canvas.export_for_ocr()
        text = pytesseract.image_to_string(ocr_ready_image).strip()
        if not text:
            return True, "(No readable text detected in the drawing.)"
        return True, text
    except Exception as exc:  # pragma: no cover -- OCR engine behaviour varies by platform
        return False, f"OCR failed: {exc}"
