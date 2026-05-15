"""
CLI entry point for PyCatPrint.
"""
import click
from pathlib import Path


@click.command()
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
@click.version_option(version='0.1.0', prog_name='PyCatPrint')
def main(input, device, darkness, speed, dither, preview):
    """
    PyCatPrint - Print images and PDFs to BLE thermal printers.
    
    This tool connects to cat printers via Bluetooth Low Energy and
    converts images/PDFs into thermal prints.
    """
    click.echo(f"PyCatPrint v0.1.0")
    click.echo(f"Input file: {input}")
    click.echo(f"Device: {device or 'Auto-scan'}")
    click.echo(f"Darkness: {darkness}")
    click.echo(f"Speed: {speed}")
    click.echo(f"Dither: {dither}")
    click.echo(f"Preview: {preview}")
    
    # TODO: Implement the actual printing logic
    click.echo("\n[Phase 1 Complete] CLI framework ready!")
    click.echo("Next: Implement BLE communication module")


if __name__ == '__main__':
    main()
