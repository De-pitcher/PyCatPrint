"""
CLI entry point for PyCatPrint.
"""
import asyncio
import sys
import logging
import click
from pathlib import Path
from pycatprint.ble import CatPrinter, DeviceNotFoundError, ConnectionError
from pycatprint.ble_mock import MockCatPrinter
from pycatprint.image_processor import ImageProcessor
from pycatprint.pdf_processor import PDFProcessor
from pycatprint.printer_commands import PrinterCommands
from pycatprint.utils import validate_input_file, print_success, print_error, print_info, print_warning


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
@click.option(
    '--mock', '-m',
    is_flag=True,
    help='Use virtual mock BLE device (hardware-less mode)'
)
def scan(timeout, mock):
    """Scan for nearby cat printer devices."""
    if mock:
        print_info("[MOCK MODE] Scanning for virtual cat printers...")
    else:
        click.echo("Scanning for cat printers...")
    
    async def do_scan():
        printer = MockCatPrinter() if mock else CatPrinter()
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


@cli.command('print')
@click.option(
    '--input', '-i',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Path to image (PNG/JPG/BMP) or PDF file'
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
    help='Show ASCII bitmap preview in terminal before printing'
)
@click.option(
    '--mock', '-m',
    is_flag=True,
    help='Use virtual mock BLE printer (simulates printing without hardware)'
)
@click.option(
    '--output-preview', '-o',
    type=click.Path(path_type=Path),
    default=None,
    help='Output PNG file path to save rendered thermal print preview'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def print_file(input, device, darkness, speed, dither, preview, mock, output_preview, verbose):
    """Print an image or PDF file to the cat printer."""
    
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('pycatprint').setLevel(logging.DEBUG)
    
    click.echo("PyCatPrint v0.1.0\n")
    if mock:
        print_info("--- [HARDWARE-LESS MOCK MODE ENABLED] ---")
    
    # Validate input file
    try:
        file_type = validate_input_file(input)
        print_info(f"Input: {input} ({file_type})")
    except Exception as e:
        print_error(f"Invalid input file: {e}")
        sys.exit(1)
    
    click.echo(f"Device: {device or ('PD01_MOCK' if mock else 'Auto-detect')}")
    click.echo(f"Settings: Darkness={darkness}, Speed={speed}, Dither={dither}")
    click.echo()
    
    async def do_print():
        printer = MockCatPrinter(device_name=device) if mock else CatPrinter(device_name=device)
        
        try:
            # Process input file into bitmap data
            image_data = bytearray()
            processor = ImageProcessor(dither_method=dither)
            
            if file_type == 'pdf':
                print_info("Processing PDF document...")
                pdf_proc = PDFProcessor()
                pages = pdf_proc.extract_pages(str(input))
                print_info(f"Loaded {len(pages)} PDF page(s)")
                
                for idx, page in enumerate(pages, 1):
                    print_info(f"Rendering PDF page {idx}/{len(pages)}...")
                    # Save temporary page image or process direct PIL image
                    resized = processor.resize_image(page)
                    gray = processor.convert_to_grayscale(resized)
                    dithered = processor.apply_dithering(gray)
                    page_bytes = processor.rasterize(dithered)
                    image_data.extend(page_bytes)
                    
                    if idx < len(pages):
                        # Insert page separator
                        image_data.extend(pdf_proc.create_page_separator(50))
            else:
                # Show ASCII preview if requested for image
                if preview:
                    print_info("Generating preview...")
                    ascii_preview = processor.get_preview_ascii(input, max_width=60)
                    click.echo("\nPreview:")
                    click.echo("=" * 60)
                    click.echo(ascii_preview)
                    click.echo("=" * 60)
                    
                    if not click.confirm("\nProceed with printing?", default=True):
                        print_info("Print cancelled by user")
                        return
                
                print_info("Processing image...")
                image_data = processor.process_image(input)
            
            print_success(f"Bitmap generated: {len(image_data)} bytes ({len(image_data) // 48} rows)")
            
            # Build print commands
            print_info("Building print commands...")
            commands = PrinterCommands.build_print_job(
                bytes(image_data), 
                darkness=darkness,
                feed_lines=100  # Feed paper after print
            )
            print_success(f"Generated {len(commands)} command packets")
            
            # Connect to printer
            print_info("Connecting to printer...")
            await printer.connect()
            print_success(f"Connected to {printer.device.name}")
            
            # Send packets
            print_info(f"Sending {len(commands)} packets to printer...")
            await printer.send_packets(commands, delay_ms=10)
            print_success("Print packets sent successfully!")
            
            # If in mock mode or output_preview specified, save rendered preview PNG
            if mock or output_preview:
                save_path = output_preview or Path("rendered_thermal_printout.png")
                if isinstance(printer, MockCatPrinter):
                    saved_file = printer.save_preview_image(save_path)
                    print_success(f"Saved rendered thermal printout preview to: {saved_file}")
            
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
@click.option(
    '--mock', '-m',
    is_flag=True,
    help='Use virtual mock BLE printer (hardware-less mode)'
)
def test(device, mock):
    """Test connection to a cat printer."""
    if mock:
        print_info("[MOCK MODE] Testing connection to virtual cat printer...\n")
    else:
        click.echo("Testing printer connection...\n")
    
    async def do_test():
        printer = MockCatPrinter(device_name=device) if mock else CatPrinter(device_name=device)
        
        try:
            # Connect
            print_info("Connecting...")
            await printer.connect()
            print_success(f"Connected to {printer.device.name}")
            print_success(f"Address: {printer.device.address}")
            print_success(f"Write characteristic: {printer.write_characteristic}")
            
            # Test is_connected property
            if printer.is_connected:
                print_success("Connection verified")
            
            # Disconnect
            await printer.disconnect()
            print_success("Disconnected successfully")
            
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
