"""
Generate test images for printer testing.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def create_test_pattern(filename='test_pattern.png', width=384, height=200):
    """Create a test pattern image with various elements."""
    
    # Create white background
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # Draw grid
    grid_size = 20
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill='lightgray', width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill='lightgray', width=1)
    
    # Draw gradient
    for i in range(128):
        color = int(i * 2)
        draw.line([(128 + i, 20), (128 + i, 60)], fill=(color, color, color))
    
    # Draw shapes
    draw.ellipse([20, 80, 80, 140], outline='black', width=2)
    draw.rectangle([100, 80, 160, 140], outline='black', width=2)
    draw.polygon([(200, 80), (230, 80), (215, 140)], outline='black', width=2)
    
    # Draw text
    try:
        draw.text((20, 160), "Cat Printer Test Pattern", fill='black')
    except:
        pass  # Font might not be available
    
    img.save(filename)
    print(f"Test pattern saved to: {filename}")
    return filename


def create_qr_test(filename='test_qr.png', width=384, height=200):
    """Create a simple QR-code-like pattern."""
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Create a checkerboard pattern
    block_size = 10
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            if (x // block_size + y // block_size) % 2 == 0:
                draw.rectangle([x, y, x + block_size, y + block_size], fill='black')
    
    img.save(filename)
    print(f"QR test pattern saved to: {filename}")
    return filename


def create_gradient_test(filename='test_gradient.png', width=384, height=200):
    """Create a gradient test image."""
    
    # Create gradient using numpy
    gradient = np.linspace(0, 255, width, dtype=np.uint8)
    img_array = np.tile(gradient, (height, 1))
    
    img = Image.fromarray(img_array, mode='L')
    img.save(filename)
    print(f"Gradient test saved to: {filename}")
    return filename


if __name__ == "__main__":
    print("Creating test images...")
    create_test_pattern()
    create_qr_test()
    create_gradient_test()
    print("\nTest images created! You can now test with:")
    print("  python -m pycatprint.test_image test_pattern.png")
    print("  python -m pycatprint.cli print-file --input test_pattern.png --preview")
