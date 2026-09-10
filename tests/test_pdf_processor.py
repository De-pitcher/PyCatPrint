"""
Unit tests for PDFProcessor module.
"""
import pytest
from pycatprint.pdf_processor import PDFProcessor


def test_pdf_processor_init():
    proc = PDFProcessor(dpi=150)
    assert proc.dpi == 150
    assert proc.BYTES_PER_ROW == 48


def test_create_page_separator():
    proc = PDFProcessor()
    sep = proc.create_page_separator(rows=10)
    assert len(sep) == 48 * 10
    assert all(b == 0 for b in sep)
