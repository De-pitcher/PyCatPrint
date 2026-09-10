"""
Test script for BLE connectivity to cat printers.

This script helps validate BLE connection, device discovery,
and basic communication.
"""
import asyncio
import logging
import sys
from pycatprint.ble import CatPrinter, DeviceNotFoundError, ConnectionError
from pycatprint.utils import print_success, print_error, print_info, print_warning


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_device_discovery():
    """Test scanning for cat printer devices."""
    print_info("Testing device discovery...")
    
    printer = CatPrinter()
    try:
        devices = await printer.discover_devices(timeout=10.0)
        
        if devices:
            print_success(f"Found {len(devices)} cat printer(s):")
            for name, address in devices:
                print(f"  - {name} ({address})")
            return devices
        else:
            print_warning("No cat printers found")
            print("Make sure your printer is:")
            print("  1. Powered on")
            print("  2. In pairing/discoverable mode")
            print("  3. Within Bluetooth range")
            return []
    except Exception as e:
        print_error(f"Discovery failed: {e}")
        return []


async def test_connection(device_name=None):
    """Test connecting to a cat printer."""
    print_info(f"Testing connection to {device_name or 'auto-detected printer'}...")
    
    printer = CatPrinter(device_name=device_name)
    
    try:
        # Connect
        await printer.connect()
        print_success("Connection established!")
        
        # Check connection status
        if printer.is_connected:
            print_success("Device is connected")
            print(f"  Write characteristic: {printer.write_characteristic}")
        
        # Disconnect
        await printer.disconnect()
        print_success("Disconnected successfully")
        
        return True
        
    except DeviceNotFoundError as e:
        print_error(f"Device not found: {e}")
        return False
    except ConnectionError as e:
        print_error(f"Connection failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_paper_feed(device_name=None):
    """Test basic paper feed command."""
    print_info("Testing paper feed...")
    
    printer = CatPrinter(device_name=device_name)
    
    try:
        await printer.connect()
        print_success("Connected")
        
        # Simple paper feed command (this is a common command pattern)
        # The actual command may vary by printer model
        feed_command = bytes([0x1B, 0x64, 0x32])  # ESC d 2 (feed 2 lines)
        
        print_info("Sending paper feed command...")
        await printer.send_command(feed_command)
        print_success("Command sent successfully")
        
        await printer.disconnect()
        return True
        
    except Exception as e:
        print_error(f"Paper feed test failed: {e}")
        if printer.is_connected:
            await printer.disconnect()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Cat Printer BLE Connection Test")
    print("=" * 60)
    print()
    
    # Test 1: Device Discovery
    print("Test 1: Device Discovery")
    print("-" * 60)
    devices = await test_device_discovery()
    print()
    
    if not devices:
        print_warning("No devices found. Cannot proceed with connection tests.")
        return
    
    # Test 2: Connection Test
    print("Test 2: Connection Test")
    print("-" * 60)
    # Use the first discovered device
    device_name = devices[0][0]
    success = await test_connection(device_name)
    print()
    
    if not success:
        print_warning("Connection test failed. Skipping paper feed test.")
        return
    
    # Test 3: Paper Feed (optional)
    print("Test 3: Paper Feed (Optional)")
    print("-" * 60)
    response = input("Do you want to test paper feed? This will advance paper. (y/N): ")
    if response.lower() == 'y':
        await test_paper_feed(device_name)
    else:
        print_info("Paper feed test skipped")
    print()
    
    print("=" * 60)
    print_success("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(0)
