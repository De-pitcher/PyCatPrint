"""
Image Processing Module for Cat Printer.

This module handles image conversion, resizing, dithering, and
rasterization for thermal printing.
"""
import logging
from typing import Tuple, Union
from pathlib import Path
from PIL import Image
import numpy as np


logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Processes images for thermal printer compatibility.
    
    - Resizes to 384px width
    - Converts to grayscale
    - Applies dithering algorithms
    - Generates binary bitmap data
    """
    
    PRINTER_WIDTH = 384  # pixels
    BYTES_PER_ROW = 48   # 384 / 8 = 48 bytes
    
    def __init__(self, dither_method: str = 'floyd-steinberg'):
        """
        Initialize the image processor.
        
        Args:
            dither_method: Dithering algorithm to use
                (floyd-steinberg, atkinson, halftone)
        """
        self.dither_method = dither_method.lower()
        
        # Validate dither method
        valid_methods = ['floyd-steinberg', 'atkinson', 'halftone']
        if self.dither_method not in valid_methods:
            raise ValueError(f"Invalid dither method. Choose from: {valid_methods}")
    
    def process_image(self, image_path: Union[str, Path]) -> bytes:
        """
        Process an image file into printer-ready binary data.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Binary bitmap data ready for printing
        """
        logger.info(f"Processing image: {image_path}")
        
        # Load image
        image = Image.open(image_path)
        logger.info(f"Loaded image: {image.size} ({image.mode})")
        
        # Resize to printer width
        image = self.resize_image(image)
        logger.info(f"Resized to: {image.size}")
        
        # Convert to grayscale
        image = self.convert_to_grayscale(image)
        logger.info("Converted to grayscale")
        
        # Apply dithering
        image = self.apply_dithering(image)
        logger.info(f"Applied {self.dither_method} dithering")
        
        # Rasterize to bytes
        data = self.rasterize(image)
        logger.info(f"Rasterized to {len(data)} bytes ({len(data) // self.BYTES_PER_ROW} rows)")
        
        return data
    
    def resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image to printer width while maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            
        Returns:
            Resized image (384px width)
        """
        original_width, original_height = image.size
        
        # Calculate new height maintaining aspect ratio
        aspect_ratio = original_height / original_width
        new_width = self.PRINTER_WIDTH
        new_height = int(new_width * aspect_ratio)
        
        # Resize using high-quality Lanczos resampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return resized
    
    def convert_to_grayscale(self, image: Image.Image) -> Image.Image:
        """
        Convert image to grayscale.
        
        Args:
            image: PIL Image object
            
        Returns:
            Grayscale image
        """
        # Convert to grayscale ('L' mode)
        if image.mode != 'L':
            image = image.convert('L')
        
        return image
    
    def apply_dithering(self, image: Image.Image) -> Image.Image:
        """
        Apply dithering algorithm to convert grayscale to 1-bit B&W.
        
        Args:
            image: Grayscale PIL Image
            
        Returns:
            1-bit black and white image
        """
        if self.dither_method == 'floyd-steinberg':
            return self._floyd_steinberg_dither(image)
        elif self.dither_method == 'atkinson':
            return self._atkinson_dither(image)
        elif self.dither_method == 'halftone':
            return self._halftone_dither(image)
        else:
            # Fallback to simple threshold
            return image.convert('1')
    
    def _floyd_steinberg_dither(self, image: Image.Image) -> Image.Image:
        """
        Apply Floyd-Steinberg dithering algorithm.
        
        Error diffusion pattern:
              * 7/16
        3/16 5/16 1/16
        
        Args:
            image: Grayscale image
            
        Returns:
            Dithered 1-bit image
        """
        # Convert to numpy array for easier manipulation
        img_array = np.array(image, dtype=np.float32)
        height, width = img_array.shape
        
        for y in range(height):
            for x in range(width):
                old_pixel = img_array[y, x]
                new_pixel = 255 if old_pixel > 127 else 0
                img_array[y, x] = new_pixel
                
                error = old_pixel - new_pixel
                
                # Distribute error to neighboring pixels
                if x + 1 < width:
                    img_array[y, x + 1] += error * 7 / 16
                if y + 1 < height:
                    if x > 0:
                        img_array[y + 1, x - 1] += error * 3 / 16
                    img_array[y + 1, x] += error * 5 / 16
                    if x + 1 < width:
                        img_array[y + 1, x + 1] += error * 1 / 16
        
        # Convert back to PIL Image
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        return Image.fromarray(img_array, mode='L').convert('1')
    
    def _atkinson_dither(self, image: Image.Image) -> Image.Image:
        """
        Apply Atkinson dithering algorithm.
        
        Error diffusion pattern (1/8 each):
              * 1 1
            1 1 1
              1
        
        Args:
            image: Grayscale image
            
        Returns:
            Dithered 1-bit image
        """
        img_array = np.array(image, dtype=np.float32)
        height, width = img_array.shape
        
        for y in range(height):
            for x in range(width):
                old_pixel = img_array[y, x]
                new_pixel = 255 if old_pixel > 127 else 0
                img_array[y, x] = new_pixel
                
                error = (old_pixel - new_pixel) / 8  # Atkinson uses 1/8
                
                # Distribute error
                if x + 1 < width:
                    img_array[y, x + 1] += error
                if x + 2 < width:
                    img_array[y, x + 2] += error
                if y + 1 < height:
                    if x > 0:
                        img_array[y + 1, x - 1] += error
                    img_array[y + 1, x] += error
                    if x + 1 < width:
                        img_array[y + 1, x + 1] += error
                if y + 2 < height:
                    img_array[y + 2, x] += error
        
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        return Image.fromarray(img_array, mode='L').convert('1')
    
    def _halftone_dither(self, image: Image.Image) -> Image.Image:
        """
        Apply ordered (Bayer) dithering for halftone effect.
        
        Uses a 4x4 Bayer matrix for threshold comparison.
        
        Args:
            image: Grayscale image
            
        Returns:
            Dithered 1-bit image
        """
        # 4x4 Bayer matrix (normalized to 0-255)
        bayer_matrix = np.array([
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ], dtype=np.float32) * 17  # Scale to 0-255 range
        
        img_array = np.array(image, dtype=np.float32)
        height, width = img_array.shape
        
        # Create threshold map by tiling the Bayer matrix
        threshold_map = np.tile(bayer_matrix, (height // 4 + 1, width // 4 + 1))
        threshold_map = threshold_map[:height, :width]
        
        # Apply threshold
        result = (img_array > threshold_map).astype(np.uint8) * 255
        
        return Image.fromarray(result, mode='L').convert('1')
    
    def rasterize(self, image: Image.Image) -> bytes:
        """
        Convert 1-bit image to byte array for printer.
        
        Each bit represents a dot: 1 = Black, 0 = White
        384 pixels = 48 bytes per row
        
        Args:
            image: 1-bit PIL Image
            
        Returns:
            Rasterized byte data
        """
        # Ensure image is in 1-bit mode
        if image.mode != '1':
            image = image.convert('1')
        
        width, height = image.size
        
        # Pad width to PRINTER_WIDTH if necessary
        if width != self.PRINTER_WIDTH:
            new_image = Image.new('1', (self.PRINTER_WIDTH, height), 1)  # White background
            new_image.paste(image, (0, 0))
            image = new_image
        
        # Convert to numpy array
        img_array = np.array(image, dtype=np.uint8)
        
        # Invert: printer expects 1=black, 0=white, but PIL gives us 0=black, 255=white
        img_array = (img_array == 0).astype(np.uint8)
        
        # Pack bits into bytes (8 pixels per byte, LSB-First for PD01)
        # From Fun Print APK: pixel 0 -> bit 0 (LSB), pixel 7 -> bit 7 (MSB)
        # numpy packbits with bitorder='little': first element -> bit 0 (LSB)
        result = []
        for row in img_array:
            row_bytes = np.packbits(row, bitorder='little')
            result.extend(row_bytes)
        
        return bytes(result)
    
    def get_preview_ascii(self, image_path: Union[str, Path], max_width: int = 80) -> str:
        """
        Generate ASCII preview of the processed image.
        
        Args:
            image_path: Path to image file
            max_width: Maximum width in characters for preview
            
        Returns:
            ASCII art string representation
        """
        # Process the image
        image = Image.open(image_path)
        image = self.resize_image(image)
        image = self.convert_to_grayscale(image)
        image = self.apply_dithering(image)
        
        # Scale down for ASCII preview
        aspect_ratio = image.height / image.width
        preview_width = min(max_width, image.width)
        preview_height = int(preview_width * aspect_ratio * 0.5)  # 0.5 for char aspect
        
        preview = image.resize((preview_width, preview_height), Image.Resampling.NEAREST)
        
        # Convert to ASCII
        ascii_chars = [' ', '█']
        img_array = np.array(preview)
        
        ascii_art = []
        for row in img_array:
            ascii_row = ''.join(ascii_chars[0 if pixel == 0 else 1] for pixel in row)
            ascii_art.append(ascii_row)
        
        return '\n'.join(ascii_art)
