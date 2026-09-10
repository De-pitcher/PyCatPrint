# 🐾 PyCatPrint

> A Python CLI tool & hardware simulator for controlling BLE thermal printers (PD01, GT01, GB02, MX11).

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build Status](https://img.shields.io/badge/tests-24%20passed-brightgreen.svg)

PyCatPrint connects to Bluetooth Low Energy (BLE) thermal printers—commonly known as **cat printers**—and converts standard images (PNG, JPG, BMP) and multi-page PDF documents into thermal prints.

It features a **Hardware-Less Virtual Mock Simulator (`--mock`)** that allows developers to process images, generate protocol packets, and render visual thermal print previews (`.png`) without physical printer hardware.

---

## ✨ Features

- 🔌 **BLE Connectivity**: Auto-discover & pair with thermal cat printers via Bluetooth Low Energy.
- 🧪 **Hardware-Less Virtual Simulator (`--mock`)**: Test commands, validate protocol byte streams, and save rendered PNG printout previews when physical hardware is unavailable.
- 🖼️ **Advanced Dithering Algorithms**:
  - **Floyd-Steinberg**: Error diffusion for high-detail photos.
  - **Atkinson**: Crisp contrast rendering.
  - **Halftone (Bayer 4x4)**: Classic dot-pattern dither.
- 📄 **PDF Document Printing**: Multi-page PDF extraction with automatic page separators.
- ⚡ **PD01 Protocol Engine**: Reverse-engineered protocol support extracted from the official *Fun Print* APK (`com/xyz/yintibao/library/V5g.java`), including CRC8 checksum calculations (polynomial `0x07`).
- 🔍 **ASCII & Visual Preview**: Inspect the 1-bit rasterized printout directly in the terminal or export PNG renders.

---

## 🖨️ Protocol & Technical Specifications

| Parameter | Specification |
|-----------|---------------|
| **Print Head Width** | 384 pixels (48 bytes per row) |
| **Color Depth** | 1-bit Monochrome (1 = Black/Print, 0 = White/No Print) |
| **Magic Header** | `0x51 0x78` ("Qx") |
| **Packet Structure** | `[0x51 0x78] [CMD] [0x00] [LEN_LO] [LEN_HI] [DATA...] [CRC8] [0xFF]` |
| **Supported Devices** | PD01, GT01, GB02, MX11, and compatible 384px BLE thermal printers |

---

## 📦 Installation

```powershell
# Clone the repository
git clone https://github.com/De-pitcher/PyCatPrint.git
cd PyCatPrint

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install package in editable mode
pip install -e .
```

---

## 🚀 Usage

### 1. Hardware-Less Simulation Mode (No Printer Required)

Test printing an image and render a virtual thermal printout PNG:

```powershell
# Print image in mock mode and export rendered preview PNG
pycatprint print -i photo.jpg --mock -o printed_preview.png

# Test virtual BLE device connection
pycatprint test --mock

# Scan for virtual devices
pycatprint scan --mock
```

### 2. Physical BLE Thermal Printing

```powershell
# Scan for nearby BLE cat printers
pycatprint scan

# Test connectivity to a specific printer
pycatprint test --device "PD01"

# Print an image file
pycatprint print -i photo.png --darkness 75 --dither floyd-steinberg

# Print a multi-page PDF document
pycatprint print -i document.pdf --darkness 60

# Display ASCII preview before printing
pycatprint print -i photo.png --preview
```

---

## 🛠️ CLI Commands & Options

```
Usage: pycatprint [OPTIONS] COMMAND [ARGS]...

Commands:
  scan   Scan for nearby cat printer devices.
  test   Test connection to a cat printer.
  print  Print an image or PDF file to the cat printer.
```

### Options for `print`:

| Flag / Option | Description | Default |
|---------------|-------------|---------|
| `-i, --input <path>` | Path to image (PNG/JPG/BMP) or PDF file (**Required**) | — |
| `-d, --device <name>` | BLE device name or MAC address | Auto-detect |
| `-m, --mock` | Run in virtual mock mode (no BLE hardware needed) | `False` |
| `-o, --output-preview <path>` | Save rendered thermal printout preview as PNG | — |
| `--darkness <0-100>` | Thermal energy quality level (maps to quality 1-5) | `50` |
| `--dither <method>` | `floyd-steinberg`, `atkinson`, or `halftone` | `floyd-steinberg` |
| `--preview` | Show terminal ASCII preview before printing | `False` |
| `-v, --verbose` | Enable debug logging | `False` |

---

## 🧪 Testing Suite

PyCatPrint includes a comprehensive pytest suite covering image binarization, dithering, PD01 protocol CRC8 validation, PDF extraction, BLE mock transport, and CLI execution.

```powershell
# Run unit test suite
.\venv\Scripts\pytest
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).

---

## 👤 Author

**Emmanwa Emmanuel** ([@De-pitcher](https://github.com/De-pitcher))
- GitHub: [https://github.com/De-pitcher](https://github.com/De-pitcher)
