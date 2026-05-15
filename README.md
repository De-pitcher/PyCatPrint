# PyCatPrint

A Python-based CLI tool for controlling BLE thermal printers (commonly known as "cat printers"). This tool enables printing of images and PDF files directly to your cat printer via Bluetooth Low Energy.

## Overview

PyCatPrint connects to BLE thermal printers and converts standard image formats (PNG, JPG) and PDF files into printer-compatible binary bitmaps. The tool handles image processing, dithering, and BLE communication to produce high-quality thermal prints.

## Features

- 🔌 **BLE Connectivity**: Auto-discover and connect to cat printers (GT01, GB02, MX11, etc.)
- 🖼️ **Image Processing**: Convert images with advanced dithering algorithms (Floyd-Steinberg, Atkinson, Halftone)
- 📄 **PDF Support**: Print multi-page PDFs with automatic page separation
- ⚙️ **Customizable Settings**: Control darkness, speed, and dithering methods
- 🔍 **Preview Mode**: Preview the binary bitmap before printing
- 🐛 **Debug Tools**: Hex dump logging and connectivity testing

## Supported Printers

- GT01
- GB02
- MX11
- Other 384-pixel width BLE thermal printers

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PyCatPrint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Print an image
python pycatprint.py --input photo.jpg

# Print a PDF
python pycatprint.py --input document.pdf

# Customize print settings
python pycatprint.py --input image.png --darkness 80 --speed 2 --dither floyd-steinberg

# Preview before printing
python pycatprint.py --input image.png --preview

# Specify device
python pycatprint.py --input image.png --device "GT01"
```

## CLI Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--input` | str | Path to image (PNG/JPG) or PDF file |
| `--device` | str | BLE device name or MAC address (optional, auto-scans by default) |
| `--darkness` | int/str | Thermal energy level: 0-100 or Light/Medium/Dark |
| `--speed` | int | Print speed: 1 (slow), 2 (medium), 3 (fast) |
| `--dither` | str | Dithering algorithm: floyd-steinberg, atkinson, halftone |
| `--preview` | flag | Show 1-bit bitmap preview before printing |

## Technical Details

- **Print Width**: 384 pixels (48 bytes per row)
- **Color Depth**: 1-bit (Black/White)
- **MTU**: ~20 bytes (packets are automatically chunked)
- **Protocol**: BLE with custom packet structure (header: 0x7E + payload + footer: 0x7E 0xEF)

## Development Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development phases and implementation plan.

## Reference

This project is inspired by and references:
- [rbaron/catprinter](https://github.com/rbaron/catprinter) - BLE protocol implementation

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
