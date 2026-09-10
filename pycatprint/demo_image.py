"""
Test script for image processing functionality.

This script helps validate image resizing, dithering algorithms,
and rasterization.
"""
import sys
from pathlib import Path
from pycatprint.image_processor import ImageProcessor
from pycatprint.utils import print_success, print_error, print_info


def test_image_processing(image_path: str, dither_method: str = 'floyd-steinberg'):
    """Test image processing with a given image."""
    
    print_info(f"Testing image processing with {dither_method} dithering")
    print(f"Input: {image_path}\n")
    
    try:
        # Create processor
        processor = ImageProcessor(dither_method=dither_method)
        
        # Process image
        print_info("Processing image...")
        data = processor.process_image(image_path)
        
        print_success(f"Image processed successfully!")
        print(f"  Output size: {len(data)} bytes")
        print(f"  Rows: {len(data) // processor.BYTES_PER_ROW}")
        print(f"  Bytes per row: {processor.BYTES_PER_ROW}")
        print()
        
        # Generate ASCII preview
        print_info("Generating ASCII preview...")
        ascii_preview = processor.get_preview_ascii(image_path, max_width=60)
        print("\nPreview:")
        print("=" * 60)
        print(ascii_preview)
        print("=" * 60)
        print()
        
        return True
        
    except Exception as e:
        print_error(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_dither_methods(image_path: str):
    """Compare all dithering methods side by side."""
    
    methods = ['floyd-steinberg', 'atkinson', 'halftone']
    
    print("Comparing dithering methods...")
    print("=" * 60)
    print()
    
    for method in methods:
        print(f"\n{method.upper()}:")
        print("-" * 60)
        
        try:
            processor = ImageProcessor(dither_method=method)
            data = processor.process_image(image_path)
            
            print_success(f"Processed: {len(data)} bytes")
            
            # Show small preview
            ascii_preview = processor.get_preview_ascii(image_path, max_width=40)
            print(ascii_preview[:400])  # First few lines
            
        except Exception as e:
            print_error(f"Failed: {e}")
        
        print()


def main():
    """Run image processing tests."""
    
    if len(sys.argv) < 2:
        print("Usage: python -m pycatprint.test_image <image_path> [dither_method]")
        print("\nDither methods: floyd-steinberg (default), atkinson, halftone")
        print("\nExample:")
        print("  python -m pycatprint.test_image photo.jpg")
        print("  python -m pycatprint.test_image photo.jpg atkinson")
        print("  python -m pycatprint.test_image photo.jpg --compare")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print_error(f"Image file not found: {image_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("Image Processing Test")
    print("=" * 60)
    print()
    
    # Check for compare mode
    if len(sys.argv) > 2 and sys.argv[2] == '--compare':
        compare_dither_methods(image_path)
    else:
        dither_method = sys.argv[2] if len(sys.argv) > 2 else 'floyd-steinberg'
        success = test_image_processing(image_path, dither_method)
        
        if success:
            print_success("All tests passed!")
        else:
            print_error("Tests failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
