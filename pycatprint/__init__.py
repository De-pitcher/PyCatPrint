"""
PyCatPrint - A Python CLI tool for controlling BLE thermal printers.
"""

from pycatprint.ble import CatPrinter, CatPrinterException, DeviceNotFoundError, ConnectionError
from pycatprint.ble_mock import MockCatPrinter
from pycatprint.image_processor import ImageProcessor
from pycatprint.pdf_processor import PDFProcessor
from pycatprint.printer_commands import PrinterCommands

__version__ = "0.1.0"
__author__ = "Emmanwa Emmanuel <emmanwa000@gmail.com>"
__license__ = "MIT"

__all__ = [
    "CatPrinter",
    "MockCatPrinter",
    "CatPrinterException",
    "DeviceNotFoundError",
    "ConnectionError",
    "ImageProcessor",
    "PDFProcessor",
    "PrinterCommands",
]
