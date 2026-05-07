#!/usr/bin/env bash
set -euo pipefail

export PYINSTALLER_CONFIG_DIR="${PWD}/.pyinstaller-cache"

python3 -m PyInstaller --noconfirm --clean --windowed --name "S26 APV to iPhone Converter" s26_apv_iphone_converter.py
