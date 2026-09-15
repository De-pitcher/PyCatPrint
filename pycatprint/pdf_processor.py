"""
PDF Processing Module for PyCatPrint.

This module handles PDF page extraction, rendering, and page separation
for thermal printers.
"""
import logging
from typing import List
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Processes PDF files for thermal printing.

    - Extracts individual pages as PIL Images
    - Generates page separator blank rows
    """

    BYTES_PER_ROW = 48  # 384 pixels / 8 bits per byte

    def __init__(self, dpi: int = 200):
        """
        Initialize the PDF processor.

        Args:
            dpi: Resolution for PDF rendering (default: 200 DPI for thermal prints)
        """
        self.dpi = dpi

    def extract_pages(self, pdf_path: str) -> List[Image.Image]:
        """
        Extract all pages from a PDF as PIL Image objects.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of PIL Image objects (one per page)
        """
        pdf_path = str(pdf_path)
        logger.info(f"Extracting pages from PDF: {pdf_path}")

        try:
            import pdf2image
            pages = pdf2image.convert_from_path(pdf_path, dpi=self.dpi)
            logger.info(f"Successfully extracted {len(pages)} page(s) using pdf2image")
            return pages
        except Exception as e:
            logger.warning(f"pdf2image extraction failed: {e}. Attempting fallback via pypdf...")

        # Fallback using pypdf to extract embedded images if poppler is unavailable
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            images = []
            for page_num, page in enumerate(reader.pages):
                for img_count, img_file in enumerate(page.images):
                    try:
                        img = Image.open(img_file.data)
                        images.append(img)
                    except Exception as img_err:
                        logger.warning(f"Could not open image on page {page_num}: {img_err}")

            if images:
                logger.info(f"Extracted {len(images)} image(s) from PDF via pypdf")
                return images
        except Exception as pypdf_err:
            logger.error(f"pypdf fallback failed: {pypdf_err}")

        raise RuntimeError(
            f"Could not render or extract images from PDF '{pdf_path}'. "
            "Please ensure poppler is installed for pdf2image, or convert the PDF pages to PNG/JPG images."
        )

    def create_page_separator(self, rows: int = 50) -> bytes:
        """
        Create blank line feed bytes to visually separate PDF pages.

        Args:
            rows: Number of blank rows to insert (default: 50)

        Returns:
            Blank row bytes (48 bytes of 0x00 per row)
        """
        return bytes([0x00] * (self.BYTES_PER_ROW * rows))
