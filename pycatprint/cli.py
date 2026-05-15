"""
CLI entry point for PyCatPrint.
"""
import asyncio
import sys
import logging
import click
from pathlib import Path
from pycatprint.ble import CatPrinter, DeviceNotFoundError, ConnectionError
from pycatprint.image_processor import ImageProcessor
from pycatprint.printer_commands import PrinterCommands
from pycatprint.utils import validate_input_file, print_success, print_error, print_info


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='0.1.0', prog_name='PyCatPrint')
def cli():
    """
    PyCatPrint - Print images and PDFs to BLE thermal printers.
    
    This tool connects to cat printers via Bluetooth Low Energy and
    converts images/PDFs into thermal prints.
    """
    pass


@cli.command()
@click.option(
    '--timeout',
    type=float,
    default=10.0,
    help='Scan timeout in seconds (default: 10.0)'
)
def scan(timeout):
    """Scan for nearby cat printer devices."""
    click.echo("Scanning for cat printers...")
    
    async def do_scan():
        printer = CatPrinter()
        devices = await printer.discover_devices(timeout=timeout)
        
        if devices:
            print_success(f"Found {len(devices)} cat printer(s):\n")
            for name, address in devices:
                click.echo(f"  • {name}")
                click.echo(f"    Address: {address}\n")
        else:
            print_info("No cat printers found.")
            click.echo("\nTroubleshooting:")
            click.echo("  1. Make sure the printer is powered on")
            click.echo("  2. Ensure Bluetooth is enabled on your computer")
            click.echo("  3. Check if the printer is in pairing mode")
            click.echo("  4. Move the printer closer to your computer")
    
    try:
        asyncio.run(do_scan())
    except KeyboardInterrupt:
        print_error("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Scan failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    '--input', '-i',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to image (PNG/JPG) or PDF file'
)
@click.option(
    '--device', '-d',
    type=str,
    default=None,
    help='BLE device name or MAC address (auto-scans if not specified)'
)
@click.option(
    '--darkness',
    type=click.IntRange(0, 100),
    default=50,
    help='Thermal energy level (0-100, default: 50)'
)
@click.option(
    '--speed',
    type=click.IntRange(1, 3),
    default=2,
    help='Print speed: 1 (slow), 2 (medium), 3 (fast)'
)
@click.option(
    '--dither',
    type=click.Choice(['floyd-steinberg', 'atkinson', 'halftone'], case_sensitive=False),
    default='floyd-steinberg',
    help='Dithering algorithm (default: floyd-steinberg)'
)
@click.option(
    '--preview',
    is_flag=True,
    help='Show 1-bit bitmap preview before printing'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def print_file(input, device, darkness, speed, dither, preview, verbose):
    """Print an image or PDF file to the cat printer."""
    
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('pycatprint').setLevel(logging.DEBUG)
    
    click.echo("PyCatPrint v0.1.0\n")
    
    # Validate input file
    try:
        file_type = validate_input_file(input)
        print_info(f"Input: {input} ({file_type})")
    except Exception as e:
        print_error(f"Invalid input file: {e}")
        sys.exit(1)
    
    click.echo(f"Device: {device or 'Auto-detect'}")
    click.echo(f"Settings: Darkness={darkness}, Speed={speed}, Dither={dither}")
    click.echo()
    
    async def do_print():
        printer = CatPrinter(device_name=device)
        
        try:
            # Show preview if requested
            if preview:
                print_info("Generating preview...")
                processor = ImageProcessor(dither_method=dither)
                ascii_preview = processor.get_preview_ascii(input, max_width=60)
                click.echo("\nPreview:")
                click.echo("=" * 60)
                click.echo(ascii_preview)
                click.echo("=" * 60)
                
                if not click.confirm("\nProceed with printing?", default=True):
                    print_info("Print cancelled by user")
                    return
            
            # Process image
            print_info("Processing image...")
            processor = ImageProcessor(dither_method=dither)
            image_data = processor.process_image(input)
            print_success(f"Image processed: {len(image_data)} bytes")
            
            # Build print commands
            print_info("Building print commands...")
            commands = PrinterCommands.build_print_job(
                image_data, 
                darkness=darkness,
                feed_lines=100  # Feed some paper after printing
            )
            print_success(f"Generated {len(commands)} commands")
            
            # Connect to printer
            print_info("Connecting to printer...")
            await printer.connect()
            print_success(f"Connected to {printer.device.name}")
            
            # Send all packets to printer (no chunking - complete packets only)
            print_info(f"Sending {len(commands)} packets to printer...")
            await printer.send_packets(commands, delay_ms=10)
            print_success("Print packets sent successfully!")
            
            # Disconnect
            await printer.disconnect()
            print_success("Print job complete!")
            
        except DeviceNotFoundError as e:
            print_error(f"Device not found: {e}")
            click.echo("\nTry running 'pycatprint scan' to find available devices")
            sys.exit(1)
        except ConnectionError as e:
            print_error(f"Connection failed: {e}")
            sys.exit(1)
        except Exception as e:
            print_error(f"Print failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    try:
        asyncio.run(do_print())
    except KeyboardInterrupt:
        print_error("\nPrint interrupted by user")
        sys.exit(1)


@cli.command()
@click.option(
    '--device', '-d',
    type=str,
    default=None,
    help='BLE device name or MAC address (auto-scans if not specified)'
)
def test(device):
    """Test connection to a cat printer."""
    click.echo("Testing printer connection...\n")
    
    async def do_test():
        printer = CatPrinter(device_name=device)
        
        try:
            # Connect
            print_info("Connecting...")
            await printer.connect()
            print_success(f"✓ Connected to {printer.device.name}")
            print_success(f"✓ Address: {printer.device.address}")
            print_success(f"✓ Write characteristic: {printer.write_characteristic}")
            
            # Test is_connected property
            if printer.is_connected:
                print_success("✓ Connection verified")
            
            # Disconnect
            await printer.disconnect()
            print_success("✓ Disconnected successfully")
            
            click.echo("\n" + "="*50)
            print_success("All connection tests passed!")
            click.echo("="*50)
            
        except DeviceNotFoundError as e:
            print_error(f"Device not found: {e}")
            click.echo("\nTry running 'pycatprint scan' to find available devices")
            sys.exit(1)
        except ConnectionError as e:
            print_error(f"Connection failed: {e}")
            sys.exit(1)
        except Exception as e:
            print_error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    try:
        asyncio.run(do_test())
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
