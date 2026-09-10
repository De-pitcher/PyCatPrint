"""
Unit tests for PyCatPrint CLI commands.
"""
import re
import pytest
from click.testing import CliRunner
from pycatprint.cli import cli


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text for reliable assertions."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert "PyCatPrint" in strip_ansi(result.output)


def test_cli_scan_mock():
    runner = CliRunner()
    result = runner.invoke(cli, ['scan', '--mock'])
    assert result.exit_code == 0
    clean_output = strip_ansi(result.output)
    assert "PD01_MOCK" in clean_output


def test_cli_test_mock():
    runner = CliRunner()
    result = runner.invoke(cli, ['test', '--mock'])
    assert result.exit_code == 0
    clean_output = strip_ansi(result.output)
    assert "All connection tests passed!" in clean_output


def test_cli_print_mock(tmp_path):
    # Create sample test image
    from PIL import Image
    img = Image.new('L', (100, 100), 128)
    img_path = tmp_path / "test_input.png"
    img.save(img_path)

    out_preview = tmp_path / "rendered.png"

    runner = CliRunner()
    result = runner.invoke(cli, [
        'print',
        '-i', str(img_path),
        '--mock',
        '-o', str(out_preview)
    ])

    assert result.exit_code == 0
    clean_output = strip_ansi(result.output)
    assert "Print job complete!" in clean_output
    assert out_preview.exists()
