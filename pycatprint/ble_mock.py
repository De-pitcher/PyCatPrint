"""
Virtual Mock BLE Driver and Thermal Printer Simulator for PyCatPrint.

Enables hardware-less testing and visual preview verification when physical
BLE cat printer hardware is unavailable.
"""
import logging
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np
from PIL import Image

from pycatprint.printer_commands import PrinterCommands

logger = logging.getLogger(__name__)


class MockCatPrinter:
    """
    Simulated BLE Cat Printer that records received packets, validates
    protocol integrity (magic headers, lengths, CRC8, footers), and renders
    the received bitmap data into a visual PNG preview image.
    """

    MOCK_DEVICE_NAME = "PD01_MOCK"
    MOCK_DEVICE_ADDRESS = "00:11:22:33:44:55"
    PRINTER_WIDTH = 384
    BYTES_PER_ROW = 48

    def __init__(self, device_name: Optional[str] = None):
        self.device_name = device_name or self.MOCK_DEVICE_NAME
        self.write_characteristic = "0000ae01-0000-1000-8000-00805f9b34fb"
        self._connected = False
        self.received_packets: List[bytes] = []
        self.received_rows: List[bytes] = []
        self.quality: int = 1
        self.feed_steps: int = 0
        self.lattice_active: bool = False

        # Device mock representation
        class MockDevice:
            name = self.MOCK_DEVICE_NAME
            address = self.MOCK_DEVICE_ADDRESS

        self.device = MockDevice()

    async def discover_devices(self, timeout: float = 10.0) -> List[Tuple[str, str]]:
        """Simulate BLE scan and return mock cat printer."""
        logger.info(f"[MOCK] Scanning for BLE devices (timeout: {timeout}s)...")
        return [(self.MOCK_DEVICE_NAME, self.MOCK_DEVICE_ADDRESS)]

    async def connect(self, retries: int = 3) -> bool:
        """Simulate connecting to the cat printer."""
        logger.info(f"[MOCK] Connecting to device {self.device_name}...")
        self._connected = True
        return True

    async def disconnect(self):
        """Simulate disconnecting from device."""
        logger.info(f"[MOCK] Disconnecting from device {self.device_name}...")
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def send_packet(self, packet: bytes, delay_ms: int = 10) -> bool:
        """
        Receive and process a PD01 protocol packet in mock mode.

        Packet format: [0x51 0x78][CMD][0x00][LEN_LO][LEN_HI][DATA][CRC8][0xFF]
        """
        if not self._connected:
            raise ConnectionError("[MOCK] Printer is not connected")

        self.received_packets.append(packet)

        # Validate packet structure
        if len(packet) < 8:
            raise ValueError(f"[MOCK] Packet too short: {len(packet)} bytes")

        if packet[:2] != PrinterCommands.MAGIC_HEADER:
            raise ValueError(f"[MOCK] Invalid magic header: {packet[:2].hex()}")

        if packet[-1] != PrinterCommands.PACKET_END:
            raise ValueError(f"[MOCK] Invalid packet footer: 0x{packet[-1]:02X}")

        cmd = packet[2]
        data_len = packet[4] | (packet[5] << 8)
        data = packet[6:6 + data_len]
        crc_received = packet[6 + data_len]

        # Check CRC8
        crc_expected = PrinterCommands.calc_crc8(data)
        if crc_received != crc_expected:
            raise ValueError(
                f"[MOCK] CRC mismatch for CMD 0x{cmd:02X}: expected 0x{crc_expected:02X}, got 0x{crc_received:02X}"
            )

        # Process specific commands
        if cmd == PrinterCommands.CMD_QUALITY:
            if len(data) == 1:
                self.quality = data[0] - 0x30
                logger.debug(f"[MOCK] Set quality: {self.quality}")
            elif len(data) == self.BYTES_PER_ROW:
                # Command 0xA2 with 48 bytes is a bitmap row
                self.received_rows.append(data)
                logger.debug(f"[MOCK] Received bitmap row {len(self.received_rows)}")
        elif cmd == PrinterCommands.CMD_FEED_PAPER:
            if len(data) >= 2:
                steps = data[0] | (data[1] << 8)
                self.feed_steps += steps
                logger.debug(f"[MOCK] Paper feed: {steps} steps")
        elif cmd == PrinterCommands.CMD_LATTICE:
            if data and data[3:6] == bytes([0x38, 0x44, 0x5F]):
                self.lattice_active = True
                logger.debug("[MOCK] Lattice initialized")
            else:
                self.lattice_active = False
                logger.debug("[MOCK] Lattice finished")

        return True

    async def send_packets(self, packets: List[bytes], delay_ms: int = 10) -> bool:
        """Send list of packets in mock mode."""
        for pkt in packets:
            await self.send_packet(pkt, delay_ms)
        return True

    def render_preview_image(self) -> Image.Image:
        """
        Reconstruct and render the printed image from received bitmap rows.

        Returns:
            PIL Image object (1-bit / L mode) of the printed result.
        """
        if not self.received_rows:
            # Return blank image if no rows received
            return Image.new('L', (self.PRINTER_WIDTH, 1), 255)

        num_rows = len(self.received_rows)
        img_data = np.full((num_rows, self.PRINTER_WIDTH), 255, dtype=np.uint8)

        for r_idx, row_bytes in enumerate(self.received_rows):
            # Unpack 48 bytes into 384 bits (bitorder='little' matches packbits in image_processor)
            bits = np.unpackbits(np.frombuffer(row_bytes, dtype=np.uint8), bitorder='little')
            # In image_processor: 1 = Black/Print, 0 = White/No print
            # For PIL grayscale image: 0 = Black, 255 = White
            img_data[r_idx, :] = np.where(bits[:self.PRINTER_WIDTH] == 1, 0, 255)

        return Image.fromarray(img_data, mode='L')

    def save_preview_image(self, output_path: Path) -> Path:
        """
        Save the reconstructed thermal printout as a PNG image file.

        Args:
            output_path: Target PNG file path

        Returns:
            Resolved Path of the saved image file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image = self.render_preview_image()
        image.save(output_path)
        logger.info(f"[MOCK] Saved thermal printout preview to {output_path}")
        return output_path
