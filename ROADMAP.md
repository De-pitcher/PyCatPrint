# Project Roadmap: Cat Printer Control Script

A technical roadmap for developing a Python-based CLI tool to control a BLE thermal printer (commonly known as a "cat printer"). The tool will accept an image or PDF file and send it to the printer.

## 1. Project Setup & Environment
**Objective**: Initialize the project structure and dependencies.

### Key Tasks:
- Create a project directory and a virtual environment (venv or conda)
- Create `requirements.txt` and `setup.py` (or `pyproject.toml`)
- Core dependencies:
  - `bleak` (for BLE communication)
  - `Pillow` (for image processing)
  - `pypdf` or `pdf2image` (for PDF handling)
  - `numpy` (for array manipulations)
  - `click` or `argparse` (for the CLI)

**Target Output**: A reproducible environment where the script can be executed.

---

## 2. Core BLE Communication Module
**Objective**: Establish a reliable Bluetooth Low Energy connection and data transfer.

### Key Tasks:
- **Device Discovery**: Scan for nearby BLE devices and filter by name (e.g., "GT01", "GB02", "MX11") or Service UUID
- **Connection Handling**: Connect to the device using `bleak`. Handle connection drops and retries
- **Characteristic Discovery**: Identify the specific Characteristic handle used for writing data (usually the "Write" or "RX" characteristic)
- **Packetization**: Implement the logic to chunk the byte data into packets
  - **Note**: The MTU (Maximum Transmission Unit) on these devices is often small (e.g., 20 bytes). The payload must be split into chunks (e.g., Header + Data)
  - **Logic**: Send packet header (e.g., 0x7E, payload length), followed by the image data chunk, and optionally a footer (e.g., 0x7E 0xEF)

---

## 3. Image Processing & Conversion
**Objective**: Convert standard images into a binary bitmap readable by the printer.

### Key Tasks:
- **Resize**: Resize the image canvas to match the printer's width. Most cat printers have a print head width of **384 pixels**
- **Grayscale Conversion**: Convert the image to grayscale
- **Binarization & Dithering**: Convert grayscale to pure Black/White (1-bit). The printer cannot print shades of gray, so dithering is essential
  - **Algorithms to implement**: Floyd-Steinberg (high quality), Atkinson, or Halftone
- **Rasterization**: Generate the byte array
  - Each bit in the byte represents a dot (1 = Black/Print, 0 = White/No print)
  - The width of 384 pixels requires **48 bytes per row** (384 / 8 = 48)

---

## 4. PDF Handling Module
**Objective**: Allow the tool to print directly from PDF files.

### Key Tasks:
- **Page Extraction**: Iterate through the pages of the PDF
- **Rendering**: Convert PDF pages into image objects (using `pdf2image` which relies on `poppler`)
- **Pagination**: Apply the same binarization logic from Step 3 to each page
- **Feed Control**: Insert a specific number of blank line feeds (`\x00` rows) between pages to separate the prints

---

## 5. CLI & Orchestration
**Objective**: Create a user-friendly interface to tie all modules together.

### Key Tasks:
**Arguments**:
- `--input` (str): Path to the image (PNG/JPG) or PDF
- `--device` (str): Optional BLE device name or MAC address (default: auto-scan)
- `--darkness` (int/str): Control the thermal energy (heat) of the print head (e.g., 0-100 or Light/Medium/Dark)
- `--speed` (int): Print speed (e.g., 1, 2, 3)
- `--dither` (str): Choose the dithering algorithm (floyd-steinberg, halftone, etc.)
- `--preview`: Flag that shows the final 1-bit bitmap in the terminal or saves it to a debug file before printing

---

## 6. Testing & Utility Tools
**Objective**: Ensure reliability and ease of debugging.

### Key Tasks:
- **Printer Validation**: A script to test basic connectivity and paper feeding without printing complex images
- **Debug Logs**: Hex dump logging to visualize the exact bytes being sent to the printer (useful for comparing against the logic in the `rbaron/catprinter` reference repo)
- **Energy Calibration**: Test different `--darkness` levels to find the sweet spot for your specific paper roll

---

## Reference Resources
- **BLE Protocol Blueprint**: Refer to the logic used in [rbaron/catprinter](https://github.com/rbaron/catprinter) (specifically `ble.py`) for how to structure packets and validate checksums
- **Image Specifics**: Ensure all processed images are exactly **384 pixels wide**. Pad with white space if necessary
