"""
BLE Communication Module for Cat Printer.

This module handles Bluetooth Low Energy connection and data transfer
to the thermal printer.
"""
import asyncio
import logging
from typing import Optional, List, Tuple
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice


logger = logging.getLogger(__name__)


class CatPrinterException(Exception):
    """Base exception for cat printer errors."""
    pass


class DeviceNotFoundError(CatPrinterException):
    """Raised when no cat printer device is found."""
    pass


class ConnectionError(CatPrinterException):
    """Raised when connection to device fails."""
    pass


class CatPrinter:
    """
    Manages BLE connection and communication with cat printers.
    
    Supported device names: GT01, GB02, MX11
    """
    
    # Common cat printer device names
    DEVICE_NAMES = ['GT01', 'GB02', 'MX11']
    
    # Packet structure constants
    PACKET_HEADER = 0x7E
    PACKET_FOOTER = [0x7E, 0xEF]
    MAX_PACKET_SIZE = 20  # MTU limitation
    
    # Common UUIDs for cat printers (may vary by model)
    WRITE_CHARACTERISTIC_UUID = "0000ae01-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHARACTERISTIC_UUID = "0000ae02-0000-1000-8000-00805f9b34fb"
    
    # Connection settings
    SCAN_TIMEOUT = 10.0  # seconds
    CONNECTION_TIMEOUT = 10.0  # seconds
    MAX_RETRIES = 3
    
    def __init__(self, device_name: Optional[str] = None):
        """
        Initialize the CatPrinter instance.
        
        Args:
            device_name: Specific device name or MAC address (optional)
        """
        self.device_name = device_name
        self.device: Optional[BLEDevice] = None
        self.client: Optional[BleakClient] = None
        self.write_characteristic = None
        self._connected = False
        
    async def discover_devices(self, timeout: float = SCAN_TIMEOUT) -> List[Tuple[str, str]]:
        """
        Scan for nearby BLE devices and filter for cat printers.
        
        Args:
            timeout: Scan duration in seconds
            
        Returns:
            List of tuples (device_name, address) for cat printers found
        """
        logger.info(f"Scanning for BLE devices (timeout: {timeout}s)...")
        devices = await BleakScanner.discover(timeout=timeout)
        
        cat_printers = []
        for device in devices:
            if device.name and any(name in device.name for name in self.DEVICE_NAMES):
                cat_printers.append((device.name, device.address))
                logger.info(f"Found cat printer: {device.name} ({device.address})")
        
        if not cat_printers:
            logger.warning("No cat printers found")
        
        return cat_printers
    
    async def _find_device(self) -> BLEDevice:
        """
        Find the target device by scanning.
        
        Returns:
            BLEDevice object
            
        Raises:
            DeviceNotFoundError: If device not found
        """
        logger.info("Searching for device...")
        devices = await BleakScanner.discover(timeout=self.SCAN_TIMEOUT)
        
        for device in devices:
            # Match by name or address
            if self.device_name:
                if (device.name and self.device_name in device.name) or \
                   (device.address and self.device_name.lower() == device.address.lower()):
                    logger.info(f"Found target device: {device.name} ({device.address})")
                    return device
            else:
                # Auto-detect any cat printer
                if device.name and any(name in device.name for name in self.DEVICE_NAMES):
                    logger.info(f"Auto-detected cat printer: {device.name} ({device.address})")
                    return device
        
        raise DeviceNotFoundError(
            f"Device '{self.device_name}' not found" if self.device_name 
            else "No cat printer found. Make sure the printer is powered on and in range."
        )
    
    async def connect(self, retries: int = MAX_RETRIES) -> bool:
        """
        Connect to the cat printer with retry logic.
        
        Args:
            retries: Number of connection retry attempts
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If connection fails after all retries
        """
        for attempt in range(retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{retries}")
                
                # Find device if not already found
                if not self.device:
                    self.device = await self._find_device()
                
                # Create client and connect
                self.client = BleakClient(
                    self.device.address,
                    timeout=self.CONNECTION_TIMEOUT
                )
                
                await self.client.connect()
                
                if not self.client.is_connected:
                    raise ConnectionError("Failed to establish connection")
                
                logger.info(f"Connected to {self.device.name} ({self.device.address})")
                
                # Discover characteristics
                await self._discover_characteristics()
                
                self._connected = True
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self.client:
                    try:
                        await self.client.disconnect()
                    except:
                        pass
                    self.client = None
                
                if attempt < retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    raise ConnectionError(f"Failed to connect after {retries} attempts: {e}")
        
        return False
    
    async def _discover_characteristics(self):
        """
        Discover and store the write characteristic.
        
        Raises:
            ConnectionError: If characteristic not found
        """
        if not self.client:
            raise ConnectionError("Not connected to device")
        
        # Try to find the write characteristic by UUID
        services = self.client.services
        
        for service in services:
            for char in service.characteristics:
                logger.debug(f"Characteristic: {char.uuid} - {char.properties}")
                
                # Look for write characteristic
                if "write" in char.properties:
                    self.write_characteristic = char.uuid
                    logger.info(f"Found write characteristic: {char.uuid}")
                    return
        
        # If specific UUID is available
        if self.WRITE_CHARACTERISTIC_UUID in [c.uuid for s in services for c in s.characteristics]:
            self.write_characteristic = self.WRITE_CHARACTERISTIC_UUID
            logger.info(f"Using standard write characteristic: {self.WRITE_CHARACTERISTIC_UUID}")
            return
        
        raise ConnectionError("Write characteristic not found")
    
    async def disconnect(self):
        """
        Disconnect from the cat printer.
        """
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from device")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        
        self._connected = False
        self.client = None
    
    async def send_data(self, data: bytes, chunk_size: int = MAX_PACKET_SIZE) -> bool:
        """
        Send data to the printer with proper packetization.
        
        Args:
            data: Raw bytes to send
            chunk_size: Maximum bytes per packet (default: 20)
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected or write fails
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to device")
        
        if not self.write_characteristic:
            raise ConnectionError("Write characteristic not available")
        
        logger.info(f"Sending {len(data)} bytes to printer...")
        
        # Split data into chunks
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunk_num = i // chunk_size + 1
            
            try:
                await self.client.write_gatt_char(
                    self.write_characteristic,
                    chunk,
                    response=False  # Write without response for speed
                )
                logger.debug(f"Sent chunk {chunk_num}/{total_chunks} ({len(chunk)} bytes)")
                
                # Small delay to avoid overwhelming the device
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Failed to send chunk {chunk_num}: {e}")
                raise ConnectionError(f"Failed to send data: {e}")
        
        logger.info("Data transmission complete")
        return True
    
    def _create_packet(self, payload: bytes) -> bytes:
        """
        Create a properly formatted packet with header and footer.
        
        Packet format: [HEADER] [LENGTH] [PAYLOAD] [FOOTER]
        
        Args:
            payload: Data payload
            
        Returns:
            Complete packet bytes
        """
        packet = bytearray()
        packet.append(self.PACKET_HEADER)  # 0x7E
        packet.append(len(payload))  # Payload length
        packet.extend(payload)  # Actual data
        packet.extend(self.PACKET_FOOTER)  # [0x7E, 0xEF]
        
        return bytes(packet)
    
    async def send_command(self, command: bytes) -> bool:
        """
        Send a command to the printer (wrapped in packet format).
        
        Args:
            command: Command bytes to send
            
        Returns:
            True if successful
        """
        packet = self._create_packet(command)
        return await self.send_data(packet)
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a device."""
        return self._connected and self.client and self.client.is_connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
