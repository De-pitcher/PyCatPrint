@echo off
echo ================================
echo PyCatPrint Setup Script
echo ================================
echo.

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Installing development dependencies...
pip install -e ".[dev]"

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo To activate the environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To run the CLI tool, use:
echo   python -m pycatprint.cli --help
echo.
pause
