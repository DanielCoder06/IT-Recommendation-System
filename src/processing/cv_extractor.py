from pathlib import Path
from src.processing.cv_text_extractor import extract_text_from_pdf

# Minimum length of text to be considered for CV extraction
MIN_TEXT_LENGTH = 200

def extract_cv_text(pdf_path: str | Path) -> str:
    """
    Extract text from a CV PDF using PyMuPDF.
    """
    text = extract_text_from_pdf(pdf_path)
    return text.strip()