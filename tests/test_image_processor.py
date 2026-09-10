"""
Unit tests for pycatprint image processing module.
"""
import pytest
import numpy as np
from PIL import Image
from pycatprint.image_processor import ImageProcessor


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample 100x100 gradient image for testing."""
    img_array = np.linspace(0, 255, 100 * 100, dtype=np.uint8).reshape((100, 100))
    image = Image.fromarray(img_array, mode='L')
    path = tmp_path / "sample_gradient.png"
    image.save(path)
    return path


def test_image_processor_init():
    proc = ImageProcessor(dither_method='floyd-steinberg')
    assert proc.dither_method == 'floyd-steinberg'
    assert proc.PRINTER_WIDTH == 384
    assert proc.BYTES_PER_ROW == 48

    with pytest.raises(ValueError):
        ImageProcessor(dither_method='invalid_method')


def test_resize_image(sample_image):
    proc = ImageProcessor()
    img = Image.open(sample_image)
    resized = proc.resize_image(img)
    assert resized.width == 384
    assert resized.height == 384  # Maintains aspect ratio (100x100 -> 384x384)


def test_convert_to_grayscale(sample_image):
    proc = ImageProcessor()
    img = Image.open(sample_image).convert('RGB')
    gray = proc.convert_to_grayscale(img)
    assert gray.mode == 'L'


@pytest.mark.parametrize('dither', ['floyd-steinberg', 'atkinson', 'halftone'])
def test_dithering_methods(sample_image, dither):
    proc = ImageProcessor(dither_method=dither)
    img = Image.open(sample_image)
    gray = proc.convert_to_grayscale(proc.resize_image(img))
    dithered = proc.apply_dithering(gray)
    assert dithered.mode == '1'
    assert dithered.width == 384


def test_rasterize(sample_image):
    proc = ImageProcessor()
    data = proc.process_image(sample_image)
    assert len(data) > 0
    assert len(data) % proc.BYTES_PER_ROW == 0
    assert len(data) // proc.BYTES_PER_ROW == 384


def test_ascii_preview(sample_image):
    proc = ImageProcessor()
    ascii_art = proc.get_preview_ascii(sample_image, max_width=40)
    assert isinstance(ascii_art, str)
    assert len(ascii_art) > 0
