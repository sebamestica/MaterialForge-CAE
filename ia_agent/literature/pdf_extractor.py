import os
from pathlib import Path
from pypdf import PdfReader

class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """Extracts text content page by page from the given PDF file."""
        if not pdf_path.exists():
            print(f"[PDFExtractor] File does not exist: {pdf_path}")
            return ""
        try:
            reader = PdfReader(str(pdf_path))
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            print(f"[PDFExtractor] Error extracting text from {pdf_path.name}: {e}")
            return ""
