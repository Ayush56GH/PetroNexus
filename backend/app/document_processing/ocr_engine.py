"""
PetroNexus OCR Engine (SIH 26121 Section 16 & 17)
Provides automatic fallback for scanned PDF documents and image reports.
Detects unselectable/scanned pages, converts page pixmaps via PyMuPDF,
and runs Tesseract OCR via pytesseract when available with graceful text recovery.
"""
import os
import io
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image
import fitz # PyMuPDF
from backend.app.utils.logger import logger

class OCREngine:

    def __init__(self):
        self._tesseract_available = False
        self._detect_tesseract()

    def _detect_tesseract(self):
        # Check standard Windows paths
        paths_to_check = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.getenv("TESSERACT_CMD", "")
        ]
        try:
            import pytesseract
            for p in paths_to_check:
                if p and Path(p).exists():
                    pytesseract.pytesseract.tesseract_cmd = p
                    self._tesseract_available = True
                    logger.info(f"Tesseract OCR binary found at: {p}")
                    return
            
            # Check PATH
            import shutil
            if shutil.which("tesseract"):
                self._tesseract_available = True
                logger.info("Tesseract OCR binary found in system PATH")
                return
        except Exception:
            pass
        self._tesseract_available = False

    def is_ocr_available(self) -> bool:
        return self._tesseract_available

    @staticmethod
    def is_scanned_document(text: str = "", image_count: int = 0) -> bool:
        """Determines if a document or page is a scanned document requiring OCR"""
        return len((text or "").strip()) < 50 or image_count > 0

    def process_page(self, page: fitz.Page, page_num: int) -> Tuple[str, bool, str, float]:
        """
        Analyzes a PDF page. If native selectable text is insufficient (< 50 chars),
        classifies as SCANNED_DOCUMENT and attempts OCR.
        Returns: (extracted_text, ocr_applied, ocr_status, confidence)
        """
        native_text = page.get_text().strip()
        
        # If native text is substantial, use native extraction
        if len(native_text) >= 50:
            return native_text, False, "NOT_REQUIRED", 0.98

        # Scanned page detected
        logger.info(f"Page {page_num} has minimal selectable text ({len(native_text)} chars). Classifying as SCANNED_DOCUMENT.")
        
        # If tesseract is available, perform OCR
        if self._tesseract_available:
            try:
                import pytesseract
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text and len(ocr_text.strip()) > len(native_text):
                    logger.info(f"OCR successfully extracted {len(ocr_text)} characters from page {page_num}")
                    return ocr_text.strip(), True, "PROCESSED", 0.88
            except Exception as e:
                logger.warning(f"OCR execution failed on page {page_num}: {e}")

        # OCR fallback: extract any text or embedded image blocks
        combined_text = native_text
        try:
            # Extract image metadata
            images = page.get_images()
            if images:
                combined_text += f"\n[Scanned Document Page {page_num} with {len(images)} embedded scanned image scans]"
        except Exception:
            pass

        return combined_text, False, "SCANNED_DOCUMENT_UNAVAILABLE", 0.65

ocr_engine = OCREngine()
