"""
Handles text extraction for Document Intelligence:
- Images (jpg/png) -> pytesseract OCR
- PDFs -> try native text extraction first (PyPDF2), fall back to OCR via pdf2image + pytesseract
  (covers scanned PDFs with no embedded text layer)
"""
import os

import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path


def extract_text_from_image(file_path: str) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    native_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    if native_text.strip():
        return native_text

    # Fallback: scanned PDF with no text layer -> rasterize pages and OCR them
    pages = convert_from_path(file_path, dpi=200)
    ocr_text = []
    for page_image in pages:
        ocr_text.append(pytesseract.image_to_string(page_image))
    return "\n".join(ocr_text)


def extract_text(file_path: str, file_type: str) -> str:
    ext = file_type.lower().lstrip(".")
    if ext in ("jpg", "jpeg", "png", "bmp", "tiff"):
        return extract_text_from_image(file_path)
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    if ext == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"Unsupported file type for extraction: {file_type}")
