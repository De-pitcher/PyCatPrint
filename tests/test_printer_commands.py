"""
Unit tests for PD01 printer protocol and packet builder.
"""
import pytest
from pycatprint.printer_commands import PrinterCommands


def test_crc8_calc():
    # Test vector for CRC8 polynomial 0x07
    data = bytes([0x31])  # Quality 1 data payload
    crc = PrinterCommands.calc_crc8(data)
    assert isinstance(crc, int)
    assert 0 <= crc <= 255


def test_create_packet():
    cmd = PrinterCommands.CMD_QUALITY
    data = bytes([0x31])
    pkt = PrinterCommands.create_packet(cmd, data)

    # Protocol structure: [0x51 0x78][CMD][0x00][LEN_LO][LEN_HI][DATA][CRC8][0xFF]
    assert pkt[:2] == PrinterCommands.MAGIC_HEADER
    assert pkt[2] == cmd
    assert pkt[3] == PrinterCommands.SEPARATOR
    assert pkt[4] == 1  # LEN_LO
    assert pkt[5] == 0  # LEN_HI
    assert pkt[6] == 0x31
    assert pkt[-1] == PrinterCommands.PACKET_END


def test_set_quality():
    pkt = PrinterCommands.set_quality(1)
    assert pkt[2] == PrinterCommands.CMD_QUALITY
    assert pkt[6] == 0x31  # 0x30 + 1


def test_get_device_state():
    pkt = PrinterCommands.get_device_state()
    assert pkt[2] == PrinterCommands.CMD_GET_STATE


def test_feed_paper():
    pkt = PrinterCommands.feed_paper(48)
    assert pkt[2] == PrinterCommands.CMD_FEED_PAPER
    assert pkt[6:8] == bytes([0x30, 0x00])  # 48 little endian


def test_draw_bitmap_validation():
    with pytest.raises(ValueError):
        PrinterCommands.draw_bitmap(bytes([0x00] * 20))  # Must be 48 bytes

    valid_row = bytes([0xFF] * 48)
    pkt = PrinterCommands.draw_bitmap(valid_row)
    assert pkt[2] == PrinterCommands.CMD_BITMAP


def test_build_print_job():
    image_data = bytes([0xAA] * (48 * 10))  # 10 rows
    commands = PrinterCommands.build_print_job(image_data, darkness=50, feed_lines=50)

    # Job sequence: Quality + LatticeInit + 10 Bitmap rows + FeedPaper + FinishLattice + GetState
    assert len(commands) == 1 + 1 + 10 + 1 + 1 + 1
    assert commands[0][2] == PrinterCommands.CMD_QUALITY
    assert commands[1][2] == PrinterCommands.CMD_LATTICE
    assert commands[2][2] == PrinterCommands.CMD_BITMAP
    assert commands[-1][2] == PrinterCommands.CMD_GET_STATE
