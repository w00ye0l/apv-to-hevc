@echo off
set PYINSTALLER_CONFIG_DIR=%CD%\.pyinstaller-cache
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "S26 APV to iPhone Converter" s26_apv_iphone_converter.py
