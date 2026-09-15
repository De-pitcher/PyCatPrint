"""
Unit tests for MockCatPrinter virtual hardware driver.
"""
import pytest
from pathlib import Path
from pycatprint.ble_mock import MockCatPrinter
from pycatprint.printer_commands import PrinterCommands


@pytest.mark.asyncio
async def test_mock_printer_connection():
    printer = MockCatPrinter()
    assert not printer.is_connected

    devices = await printer.discover_devices()
    assert len(devices) == 1
    assert devices[0][0] == MockCatPrinter.MOCK_DEVICE_NAME

    connected = await printer.connect()
    assert connected
    assert printer.is_connected

    await printer.disconnect()
    assert not printer.is_connected


@pytest.mark.asyncio
async def test_mock_printer_packet_processing(tmp_path):
    printer = MockCatPrinter()
    await printer.connect()

    # Build print job (5 rows of test bitmap)
    test_rows = bytes([0b10101010] * (48 * 5))
    packets = PrinterCommands.build_print_job(test_rows, darkness=50, feed_lines=20)

    success = await printer.send_packets(packets)
    assert success
    assert len(printer.received_packets) == len(packets)
    assert len(printer.received_rows) == 5

    # Render image and save preview
    preview_path = tmp_path / "mock_output.png"
    saved = printer.save_preview_image(preview_path)
    assert saved.exists()
    assert saved.stat().st_size > 0


@pytest.mark.asyncio
async def test_mock_printer_invalid_packet():
    printer = MockCatPrinter()
    await printer.connect()

    with pytest.raises(ValueError, match="Invalid magic header"):
        await printer.send_packet(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF]))
