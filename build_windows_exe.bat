@echo off
set PYINSTALLER_CONFIG_DIR=%CD%\.pyinstaller-cache
set EXTRA_ARGS=
if exist "vendor\ffmpeg\windows\bin\ffmpeg.exe" if exist "vendor\ffmpeg\windows\bin\ffprobe.exe" set EXTRA_ARGS=--add-binary "vendor\ffmpeg\windows\bin\ffmpeg.exe;bin" --add-binary "vendor\ffmpeg\windows\bin\ffprobe.exe;bin"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "S26 APV to iPhone Converter" %EXTRA_ARGS% s26_apv_iphone_converter.py
