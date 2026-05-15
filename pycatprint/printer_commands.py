"""
Printer Command Protocol for PD01 Cat Printer.

This module defines the command structure and protocol
for communicating with PD01 thermal printers.

**PROTOCOL EXTRACTED FROM FUN PRINT APK DECOMPILATION**
Source: com/xyz/yintibao/library/V5g.java
"""
import struct
from typing import List


class PrinterCommands:
    """
    PD01 Printer command codes and packet builders.
    
    Protocol: [0x51 0x78][CMD][0x00][LEN_LO][LEN_HI][DATA][CRC8][0xFF]
    
    **Verified command codes from Fun Print APK:**
    - CMD 0xA2: Set quality / Send bitmap row
    - CMD 0xA1: Feed paper  
    - CMD 0xA3: Get device state
    - CMD 0xA6: Print lattice (initialization)
    - CMD 0xA9: Update device
    - CMD 0xAE: Flow control (from notifications)
    """
    
    # Packet delimiters
    MAGIC_HEADER = bytes([0x51, 0x78])  # "Qx" magic header
    PACKET_END = 0xFF
    SEPARATOR = 0x00  # Fixed separator after CMD
    
    # Command codes (from APK decompilation)
    CMD_QUALITY = 0xA2       # Set quality
    CMD_BITMAP = 0xA2        # Send bitmap row (same as quality)
    CMD_FEED_PAPER = 0xA1    # Feed paper
    CMD_GET_STATE = 0xA3     # Get device state
    CMD_LATTICE = 0xA6       # Print lattice init
    CMD_UPDATE = 0xA9        # Update device
    
    @staticmethod
    def calc_crc8(data: bytes) -> int:
        """
        Calculate CRC8 checksum using polynomial 0x07.
        
        This is the PD01-specific CRC algorithm that validates
        the data payload only (not the entire packet).
        
        Args:
            data: Data bytes to checksum
            
        Returns:
            CRC8 value (0x00-0xFF)
        """
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    @staticmethod
    def create_packet(command: int, data: bytes = b'') -> bytes:
        """
        Create a properly formatted PD01 command packet.
        
        Packet structure:
        [0x51 0x78] [CMD] [0x00] [LEN_LO] [LEN_HI] [DATA...] [CRC8] [0xFF]
        
        Args:
            command: Command code
            data: Command data payload
            
        Returns:
            Complete packet bytes
        """
        packet = bytearray()
        
        # Magic header: 0x51 0x78
        packet.extend(PrinterCommands.MAGIC_HEADER)
        
        # Command byte
        packet.append(command)
        
        # Fixed separator: 0x00
        packet.append(PrinterCommands.SEPARATOR)
        
        # Data length (little-endian 16-bit: LEN_LO, LEN_HI)
        data_len = len(data)
        packet.append(data_len & 0xFF)         # Low byte
        packet.append((data_len >> 8) & 0xFF)  # High byte
        
        # Add data payload
        packet.extend(data)
        
        # Calculate CRC8 of data payload only
        crc = PrinterCommands.calc_crc8(data)
        packet.append(crc)
        
        # Magic footer: 0xFF
        packet.append(PrinterCommands.PACKET_END)
        
        return bytes(packet)
    
    @staticmethod
    def set_quality(quality: int = 1) -> bytes:
        """
        Set print quality (CMD 0xA2).
        
        From APK: quality1 = {81, 120, -92, 0, 1, 0, 49, -105, -1}
                           = {51  78   A2 00 01 00  31   97   FF}
        
        Args:
            quality: Quality level (1-5, default: 1)
                    1 = quality1 (data: 0x31)
                    2 = quality2 (data: 0x32)
                    3 = quality3 (data: 0x33)
                    4 = quality4 (data: 0x34)
                    5 = quality5 (data: 0x35)
        
        Returns:
            Command packet
        """
        quality_data = bytes([0x30 + quality])  # 0x31 for quality 1, etc.
        return PrinterCommands.create_packet(PrinterCommands.CMD_QUALITY, quality_data)
    
    @staticmethod
    def get_device_state() -> bytes:
        """
        Get device state (CMD 0xA3).
        
        From APK: {81, 120, -93, 0, 1, 0, 0, 0, -1}
                = {51  78   A3 00 01 00 00 00  FF}
        
        Returns:
            Command packet
        """
        data = bytes([0x00])
        return PrinterCommands.create_packet(PrinterCommands.CMD_GET_STATE, data)
    
    @staticmethod
    def print_lattice_init() -> bytes:
        """
        Initialize print lattice (CMD 0xA6).
        
        From APK: {81, 120, -90, 0, 11, 0, -86, 85, 23, 56, 68, 95, 95, 95, 68, 56, 44, -95, -1}
                = {51  78   A6 00 0B 00  AA  55  17  38  44  5F  5F  5F  44  38  2C  A1   FF}
        
        Returns:
            Command packet
        """
        data = bytes([0xAA, 0x55, 0x17, 0x38, 0x44, 0x5F, 0x5F, 0x5F, 0x44, 0x38, 0x2C])
        return PrinterCommands.create_packet(PrinterCommands.CMD_LATTICE, data)
    
    @staticmethod
    def finish_lattice() -> bytes:
        """
        Finish print lattice (CMD 0xA6).
        
        From APK: {81, 120, -90, 0, 11, 0, -86, 85, 23, 0, 0, 0, 0, 0, 0, 0, 23, 17, -1}
                = {51  78   A6 00 0B 00  AA  55  17  00 00 00 00 00 00 00  17  11   FF}
        
        Returns:
            Command packet
        """
        data = bytes([0xAA, 0x55, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x17])
        return PrinterCommands.create_packet(PrinterCommands.CMD_LATTICE, data)
    
    @staticmethod
    def draw_bitmap(row_data: bytes) -> bytes:
        """
        Send a single row of bitmap data (CMD 0xA2).
        
        Args:
            row_data: 48 bytes representing one row (384 pixels)
            
        Returns:
            Command packet
        """
        if len(row_data) != 48:
            raise ValueError(f"Row data must be exactly 48 bytes, got {len(row_data)}")
        
        return PrinterCommands.create_packet(PrinterCommands.CMD_BITMAP, row_data)
    
    @staticmethod
    def feed_paper(steps: int = 48) -> bytes:
        """
        Feed paper forward (CMD 0xA1).
        
        From APK: {81, 120, -95, 0, 2, 0, 48, 0, -7, -1}
                = {51  78   A1 00 02 00  30 00  F9  FF}
        
        Args:
            steps: Number of steps to feed (default: 48 = 0x30)
        
        Returns:
            Command packet
        """
        # Steps as 16-bit value (little-endian)
        data = struct.pack('<H', steps)
        return PrinterCommands.create_packet(PrinterCommands.CMD_FEED_PAPER, data)
    
    @staticmethod
    def build_print_job(image_data: bytes, darkness: int = 50, feed_lines: int = 100) -> List[bytes]:
        """
        Build a complete print job with CORRECT PD01 sequence.
        
        **VERIFIED SEQUENCE FROM FUN PRINT APK:**
        1. Set Quality (CMD 0xA2)
        2. Print Lattice Init (CMD 0xA6)
        3. Send bitmap rows (CMD 0xA2)
        4. Feed paper (CMD 0xA1) - multiple times
        5. Finish Lattice (CMD 0xA6)
        6. Get Device State (CMD 0xA3)
        
        Args:
            image_data: Raw bitmap data (must be multiple of 48 bytes)
            darkness: Quality level (0-100, mapped to 1-5)
            feed_lines: Number of steps to feed after printing
            
        Returns:
            List of command packets to send in sequence
        """
        commands = []
        
        # Map darkness (0-100) to quality (1-5)
        quality = max(1, min(5, int((darkness / 100.0) * 5) + 1))
        
        # === PREAMBLE SEQUENCE (from Fun Print APK) ===
        
        # 1. Set quality
        commands.append(PrinterCommands.set_quality(quality))
        
        # 2. Print Lattice init (initialization pattern)
        commands.append(PrinterCommands.print_lattice_init())
        
        # === BITMAP DATA ===
        
        # 3. Send bitmap data row by row
        rows = len(image_data) // 48
        for i in range(rows):
            row_start = i * 48
            row_end = row_start + 48
            row_data = image_data[row_start:row_end]
            commands.append(PrinterCommands.draw_bitmap(row_data))
        
        # === POSTAMBLE ===
        
        # 4. Feed paper (APK sends multiple feed commands based on paperNum)
        # We'll send one feed command with the specified steps
        feed_steps = max(1, min(65535, feed_lines))
        commands.append(PrinterCommands.feed_paper(feed_steps))
        
        # 5. Finish Lattice
        commands.append(PrinterCommands.finish_lattice())
        
        # 6. Get Device State (final command)
        commands.append(PrinterCommands.get_device_state())
        
        return commands
