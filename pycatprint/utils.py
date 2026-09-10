"""
Utility functions for PyCatPrint.
"""
import sys
from pathlib import Path
import click


def _safe_print(text: str, file=None):
    """
    Safely print text using click.echo, falling back to ASCII equivalents if terminal
    encoding does not support unicode characters (e.g. cp1252 on Windows).
    """
    try:
        click.echo(text, file=file)
    except Exception:
        encoding = getattr(sys.stdout, 'encoding', 'ascii') or 'ascii'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        click.echo(safe_text, file=file)


def validate_input_file(file_path: Path) -> str:
    """
    Validate input file exists and determine file type.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        File type: 'image' or 'pdf'
        
    Raises:
        ValueError: If file type is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    suffix = file_path.suffix.lower()
    
    if suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
        return 'image'
    elif suffix == '.pdf':
        return 'pdf'
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def hex_dump(data: bytes, width: int = 16) -> str:
    """
    Create a hex dump string for debugging.
    
    Args:
        data: Bytes to dump
        width: Number of bytes per line
        
    Returns:
        Formatted hex dump string
    """
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{i:04X}  {hex_part:<{width*3}}  {ascii_part}')
    return '\n'.join(lines)


def print_success(message: str):
    """Print success message in green."""
    from colorama import Fore, Style, init
    init(autoreset=True)
    _safe_print(f"{Fore.GREEN}[+] {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message in red."""
    from colorama import Fore, Style, init
    init(autoreset=True)
    _safe_print(f"{Fore.RED}[x] {message}{Style.RESET_ALL}", file=sys.stderr)


def print_warning(message: str):
    """Print warning message in yellow."""
    from colorama import Fore, Style, init
    init(autoreset=True)
    _safe_print(f"{Fore.YELLOW}[!] {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message in cyan."""
    from colorama import Fore, Style, init
    init(autoreset=True)
    _safe_print(f"{Fore.CYAN}[i] {message}{Style.RESET_ALL}")
