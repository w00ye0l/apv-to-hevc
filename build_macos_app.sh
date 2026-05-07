#!/usr/bin/env bash
set -euo pipefail

export PYINSTALLER_CONFIG_DIR="${PWD}/.pyinstaller-cache"

extra_args=()
if [[ -x "vendor/ffmpeg/macos/bin/ffmpeg" && -x "vendor/ffmpeg/macos/bin/ffprobe" ]]; then
  extra_args+=(--add-binary "vendor/ffmpeg/macos/bin/ffmpeg:bin")
  extra_args+=(--add-binary "vendor/ffmpeg/macos/bin/ffprobe:bin")
fi

python3 -m PyInstaller --noconfirm --clean --windowed --name "S26 APV to iPhone Converter" "${extra_args[@]}" s26_apv_iphone_converter.py
