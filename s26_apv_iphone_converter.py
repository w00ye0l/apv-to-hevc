#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S26 APV to iPhone Converter.

Standard-library tkinter GUI for converting Samsung APV/apv1 videos to
iPhone-friendly MP4 files through FFmpeg.
"""

from __future__ import annotations

import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import locale
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


APP_NAME = "S26 APV to iPhone Converter"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}

LANGUAGE_CODES = ("ko", "en", "ja")
LANGUAGE_NAMES = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
}

ENCODER_CPU = "hevc_cpu"
ENCODER_NVENC = "hevc_nvenc"
ENCODER_H264 = "h264_sdr"
ENCODER_KEYS = (ENCODER_CPU, ENCODER_NVENC, ENCODER_H264)

QUALITY_MASTER = "master"
QUALITY_RECOMMENDED = "recommended"
QUALITY_BALANCED = "balanced"
QUALITY_SMALL = "small"
QUALITY_KEYS = (QUALITY_MASTER, QUALITY_RECOMMENDED, QUALITY_BALANCED, QUALITY_SMALL)

RESOLUTION_ORIGINAL = "original"
RESOLUTION_1080P = "1080p"
RESOLUTION_KEYS = (RESOLUTION_ORIGINAL, RESOLUTION_1080P)

WINDOWS_SUFFIX = "_windows"

CPU_QUALITY = {
    QUALITY_MASTER: {"crf": "18", "preset": "slow"},
    QUALITY_RECOMMENDED: {"crf": "20", "preset": "medium"},
    QUALITY_BALANCED: {"crf": "23", "preset": "medium"},
    QUALITY_SMALL: {"crf": "26", "preset": "fast"},
}

NVENC_QUALITY = {
    QUALITY_MASTER: {"b:v": "28M", "maxrate": "45M", "bufsize": "56M"},
    QUALITY_RECOMMENDED: {"b:v": "18M", "maxrate": "30M", "bufsize": "36M"},
    QUALITY_BALANCED: {"b:v": "12M", "maxrate": "20M", "bufsize": "24M"},
    QUALITY_SMALL: {"b:v": "8M", "maxrate": "14M", "bufsize": "16M"},
}

TEXTS = {
    "ko": {
        "window.title": APP_NAME,
        "title": "S26 APV → iPhone / Windows 변환기",
        "language": "언어",
        "section.files": "변환할 영상 파일",
        "section.paths": "ffmpeg와 출력 위치",
        "section.options": "변환 옵션",
        "section.progress": "변환 진행",
        "section.log": "로그",
        "button.add_files": "파일 추가",
        "button.add_folder": "폴더 추가",
        "button.remove": "선택 제거",
        "button.clear": "전체 비우기",
        "button.open_selected": "선택 출력 위치 열기",
        "button.select": "선택",
        "button.auto_detect": "자동 탐색",
        "button.choose_folder": "폴더 선택",
        "button.open_folder": "출력 폴더 열기",
        "button.start": "변환 시작",
        "button.stop": "중지",
        "button.save_log": "로그 저장",
        "column.name": "파일명",
        "column.path": "전체 경로",
        "column.status": "상태",
        "column.output": "출력 파일",
        "label.ffmpeg": "ffmpeg",
        "label.ffprobe": "ffprobe",
        "label.suffix": "파일명 접미사",
        "label.encoder": "프리셋",
        "label.quality": "화질",
        "label.resolution": "해상도",
        "label.current_file": "현재 파일",
        "radio.source": "원본 폴더에 저장",
        "radio.folder": "별도 출력 폴더",
        "check.overwrite": "기존 출력 파일 덮어쓰기",
        "check.hdr": "BT.2020 HLG HDR 메타데이터 유지",
        "check.windows_copy": "Windows 재생용 H.264 SDR 파일도 함께 만들기",
        "help.cpu": "기본 추천: iPhone/HDR 고화질 HEVC 10-bit / CRF 20 / 원본 해상도 / FPS 무변경",
        "help.nvenc": "NVIDIA GPU/드라이버가 지원될 때 빠르게 동작하는 iPhone/HDR HEVC 프리셋입니다.",
        "help.h264": "Windows 기본 플레이어 호환성 우선 프리셋입니다. HDR 색감은 HEVC HDR 파일과 다르게 보일 수 있습니다.",
        "encoder.hevc_cpu": "iPhone / HDR 고화질 HEVC",
        "encoder.hevc_nvenc": "iPhone / HDR HEVC - NVIDIA 빠른 변환",
        "encoder.h264_sdr": "Windows 호환 H.264 SDR",
        "quality.master": "원본급",
        "quality.recommended": "고화질 권장",
        "quality.balanced": "균형",
        "quality.small": "용량 절약",
        "resolution.original": "원본 해상도 유지",
        "resolution.1080p": "1080p로 줄이기",
        "status.waiting": "대기",
        "status.idle": "대기 중",
        "status.converting": "변환 중",
        "status.completed": "완료",
        "status.failed": "실패",
        "status.skipped": "건너뜀",
        "status.stopped": "중지됨",
        "status.user_stopped": "사용자 중지",
        "status.done": "작업 완료",
        "progress.zero": "0%",
        "eta.idle": "예상 남은 시간: -",
        "eta.calculating": "예상 남은 시간: 계산 중",
        "eta.remaining": "예상 남은 시간: {time}",
        "eta.done": "예상 남은 시간: 00:00",
        "speed": "속도",
        "summary": "완료 {completed} / 실패 {failed} / 건너뜀 {skipped}",
        "ffmpeg.before": "ffmpeg 확인 전",
        "ffmpeg.missing": "ffmpeg를 찾지 못했습니다. 직접 선택해 주세요.",
        "ffmpeg.detected": "ffmpeg 감지됨",
        "ffprobe.detected": "ffprobe 감지됨",
        "ffprobe.missing": "ffprobe 없음: 진행률과 검증이 제한될 수 있음",
        "ffmpeg.apv": "APV 입력은 FFmpeg 8.0 이상 권장",
        "task.primary": "기본 출력",
        "task.windows": "Windows용 H.264 SDR",
    },
    "en": {
        "window.title": APP_NAME,
        "title": "S26 APV → iPhone / Windows Converter",
        "language": "Language",
        "section.files": "Video files to convert",
        "section.paths": "FFmpeg and output location",
        "section.options": "Conversion options",
        "section.progress": "Conversion progress",
        "section.log": "Log",
        "button.add_files": "Add files",
        "button.add_folder": "Add folder",
        "button.remove": "Remove selected",
        "button.clear": "Clear all",
        "button.open_selected": "Open selected output",
        "button.select": "Choose",
        "button.auto_detect": "Auto detect",
        "button.choose_folder": "Choose folder",
        "button.open_folder": "Open output folder",
        "button.start": "Start conversion",
        "button.stop": "Stop",
        "button.save_log": "Save log",
        "column.name": "File name",
        "column.path": "Full path",
        "column.status": "Status",
        "column.output": "Output files",
        "label.ffmpeg": "ffmpeg",
        "label.ffprobe": "ffprobe",
        "label.suffix": "File suffix",
        "label.encoder": "Preset",
        "label.quality": "Quality",
        "label.resolution": "Resolution",
        "label.current_file": "Current file",
        "radio.source": "Save next to source",
        "radio.folder": "Use output folder",
        "check.overwrite": "Overwrite existing output files",
        "check.hdr": "Keep BT.2020 HLG HDR metadata",
        "check.windows_copy": "Also create a Windows-playable H.264 SDR file",
        "help.cpu": "Recommended: iPhone/HDR high-quality HEVC 10-bit / CRF 20 / original resolution / unchanged FPS",
        "help.nvenc": "Fast iPhone/HDR HEVC preset when NVIDIA GPU and drivers support NVENC.",
        "help.h264": "Best compatibility for Windows built-in playback. HDR color may look different from the HEVC HDR file.",
        "encoder.hevc_cpu": "iPhone / HDR high-quality HEVC",
        "encoder.hevc_nvenc": "iPhone / HDR HEVC - NVIDIA fast",
        "encoder.h264_sdr": "Windows-compatible H.264 SDR",
        "quality.master": "Master quality",
        "quality.recommended": "High quality",
        "quality.balanced": "Balanced",
        "quality.small": "Smaller file",
        "resolution.original": "Keep original resolution",
        "resolution.1080p": "Downscale to 1080p",
        "status.waiting": "Waiting",
        "status.idle": "Idle",
        "status.converting": "Converting",
        "status.completed": "Done",
        "status.failed": "Failed",
        "status.skipped": "Skipped",
        "status.stopped": "Stopped",
        "status.user_stopped": "Stopped by user",
        "status.done": "Finished",
        "progress.zero": "0%",
        "eta.idle": "ETA: -",
        "eta.calculating": "ETA: calculating",
        "eta.remaining": "ETA: {time}",
        "eta.done": "ETA: 00:00",
        "speed": "speed",
        "summary": "Done {completed} / failed {failed} / skipped {skipped}",
        "ffmpeg.before": "ffmpeg not checked yet",
        "ffmpeg.missing": "ffmpeg was not found. Please choose it manually.",
        "ffmpeg.detected": "ffmpeg detected",
        "ffprobe.detected": "ffprobe detected",
        "ffprobe.missing": "ffprobe missing: progress and verification may be limited",
        "ffmpeg.apv": "FFmpeg 8.0 or newer is recommended for APV input",
        "task.primary": "Primary output",
        "task.windows": "Windows H.264 SDR",
    },
    "ja": {
        "window.title": APP_NAME,
        "title": "S26 APV → iPhone / Windows 変換ツール",
        "language": "言語",
        "section.files": "変換する動画ファイル",
        "section.paths": "FFmpeg と出力先",
        "section.options": "変換オプション",
        "section.progress": "変換の進行状況",
        "section.log": "ログ",
        "button.add_files": "ファイルを追加",
        "button.add_folder": "フォルダを追加",
        "button.remove": "選択を削除",
        "button.clear": "すべてクリア",
        "button.open_selected": "選択した出力先を開く",
        "button.select": "選択",
        "button.auto_detect": "自動検出",
        "button.choose_folder": "フォルダ選択",
        "button.open_folder": "出力フォルダを開く",
        "button.start": "変換開始",
        "button.stop": "停止",
        "button.save_log": "ログ保存",
        "column.name": "ファイル名",
        "column.path": "フルパス",
        "column.status": "状態",
        "column.output": "出力ファイル",
        "label.ffmpeg": "ffmpeg",
        "label.ffprobe": "ffprobe",
        "label.suffix": "ファイル名の接尾辞",
        "label.encoder": "プリセット",
        "label.quality": "画質",
        "label.resolution": "解像度",
        "label.current_file": "現在のファイル",
        "radio.source": "元のフォルダに保存",
        "radio.folder": "別の出力フォルダ",
        "check.overwrite": "既存の出力ファイルを上書き",
        "check.hdr": "BT.2020 HLG HDR メタデータを保持",
        "check.windows_copy": "Windows 再生用 H.264 SDR ファイルも作成",
        "help.cpu": "推奨: iPhone/HDR 高画質 HEVC 10-bit / CRF 20 / 元の解像度 / FPS 変更なし",
        "help.nvenc": "NVIDIA GPU/ドライバが対応している場合に高速な iPhone/HDR HEVC プリセットです。",
        "help.h264": "Windows 標準プレイヤーでの互換性を優先します。HDR の色味は HEVC HDR ファイルと異なる場合があります。",
        "encoder.hevc_cpu": "iPhone / HDR 高画質 HEVC",
        "encoder.hevc_nvenc": "iPhone / HDR HEVC - NVIDIA 高速",
        "encoder.h264_sdr": "Windows 互換 H.264 SDR",
        "quality.master": "マスター品質",
        "quality.recommended": "高画質推奨",
        "quality.balanced": "バランス",
        "quality.small": "容量節約",
        "resolution.original": "元の解像度を維持",
        "resolution.1080p": "1080p に縮小",
        "status.waiting": "待機",
        "status.idle": "待機中",
        "status.converting": "変換中",
        "status.completed": "完了",
        "status.failed": "失敗",
        "status.skipped": "スキップ",
        "status.stopped": "停止",
        "status.user_stopped": "ユーザー停止",
        "status.done": "作業完了",
        "progress.zero": "0%",
        "eta.idle": "残り時間: -",
        "eta.calculating": "残り時間: 計算中",
        "eta.remaining": "残り時間: {time}",
        "eta.done": "残り時間: 00:00",
        "speed": "速度",
        "summary": "完了 {completed} / 失敗 {failed} / スキップ {skipped}",
        "ffmpeg.before": "ffmpeg 未確認",
        "ffmpeg.missing": "ffmpeg が見つかりません。手動で選択してください。",
        "ffmpeg.detected": "ffmpeg 検出済み",
        "ffprobe.detected": "ffprobe 検出済み",
        "ffprobe.missing": "ffprobe なし: 進行率と検証が制限される場合があります",
        "ffmpeg.apv": "APV 入力には FFmpeg 8.0 以上を推奨",
        "task.primary": "通常出力",
        "task.windows": "Windows 用 H.264 SDR",
    },
}

MESSAGES = {
    "ko": {
        "list_locked": "변환 중에는 목록을 수정할 수 없습니다.",
        "no_files": "변환할 영상 파일을 추가해 주세요.",
        "output_folder_required": "별도 출력 폴더를 선택해 주세요.",
        "continue_anyway": "{warning}\n\n그래도 계속할까요?",
        "ffmpeg_missing": (
            "ffmpeg 실행 파일을 찾을 수 없습니다.\n"
            "ffmpeg 위치를 선택하세요.\n"
            "예: C:\\ffmpeg\\bin\\ffmpeg.exe 또는 /opt/homebrew/bin/ffmpeg"
        ),
        "output_folder_create_failed": "출력 폴더를 만들 수 없습니다:\n{error}",
        "same_output": "출력 파일이 원본 파일과 같습니다. 접미사나 출력 폴더를 변경해 주세요.",
        "output_exists": "출력 파일이 이미 존재하여 건너뜁니다. 덮어쓰려면 옵션을 체크하세요.",
        "done": "변환 작업이 완료되었습니다.",
        "open_folder_none": "열 출력 폴더가 없습니다.",
        "open_folder_failed": "폴더를 열 수 없습니다:\n{error}",
        "select_file_first": "파일 목록에서 항목을 선택해 주세요.",
        "no_output_path": "아직 출력 파일 경로가 없습니다.",
        "open_output_failed": "출력 위치를 열 수 없습니다:\n{error}",
        "log_saved": "로그를 저장했습니다.",
        "log_save_failed": "로그 저장 실패:\n{error}",
    },
    "en": {
        "list_locked": "You cannot change the file list while conversion is running.",
        "no_files": "Please add video files to convert.",
        "output_folder_required": "Please choose a separate output folder.",
        "continue_anyway": "{warning}\n\nContinue anyway?",
        "ffmpeg_missing": (
            "The ffmpeg executable could not be found.\n"
            "Please choose the ffmpeg location.\n"
            "Example: C:\\ffmpeg\\bin\\ffmpeg.exe or /opt/homebrew/bin/ffmpeg"
        ),
        "output_folder_create_failed": "Could not create the output folder:\n{error}",
        "same_output": "The output file is the same as the source file. Change the suffix or output folder.",
        "output_exists": "Output file already exists and was skipped. Enable overwrite to replace it.",
        "done": "Conversion finished.",
        "open_folder_none": "There is no output folder to open.",
        "open_folder_failed": "Could not open the folder:\n{error}",
        "select_file_first": "Please select an item in the file list.",
        "no_output_path": "There is no output path yet.",
        "open_output_failed": "Could not open the output location:\n{error}",
        "log_saved": "Log saved.",
        "log_save_failed": "Could not save the log:\n{error}",
    },
    "ja": {
        "list_locked": "変換中はファイル一覧を変更できません。",
        "no_files": "変換する動画ファイルを追加してください。",
        "output_folder_required": "別の出力フォルダを選択してください。",
        "continue_anyway": "{warning}\n\nこのまま続行しますか？",
        "ffmpeg_missing": (
            "ffmpeg 実行ファイルが見つかりません。\n"
            "ffmpeg の場所を選択してください。\n"
            "例: C:\\ffmpeg\\bin\\ffmpeg.exe または /opt/homebrew/bin/ffmpeg"
        ),
        "output_folder_create_failed": "出力フォルダを作成できません:\n{error}",
        "same_output": "出力ファイルが元ファイルと同じです。接尾辞または出力フォルダを変更してください。",
        "output_exists": "出力ファイルが既に存在するためスキップしました。上書きするにはオプションを有効にしてください。",
        "done": "変換が完了しました。",
        "open_folder_none": "開く出力フォルダがありません。",
        "open_folder_failed": "フォルダを開けません:\n{error}",
        "select_file_first": "ファイル一覧から項目を選択してください。",
        "no_output_path": "まだ出力ファイルのパスがありません。",
        "open_output_failed": "出力先を開けません:\n{error}",
        "log_saved": "ログを保存しました。",
        "log_save_failed": "ログ保存に失敗しました:\n{error}",
    },
}

TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
OUT_TIME_RE = re.compile(r"out_time=(\d+):(\d+):(\d+(?:\.\d+)?)")
DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
SPEED_RE = re.compile(r"speed=\s*([0-9.]+x)")
VERSION_RE = re.compile(r"ffmpeg version\s+([0-9]+)(?:\.([0-9]+))?", re.IGNORECASE)


@dataclass
class ConversionOptions:
    ffmpeg_path: Path
    ffprobe_path: Optional[Path]
    output_mode_source: bool
    output_folder: Optional[Path]
    suffix: str
    encoder: str
    quality: str
    resolution: str
    keep_hdr_metadata: bool
    make_windows_copy: bool
    overwrite: bool


@dataclass
class FileResult:
    input_path: Path
    output_path: Optional[Path]
    status: str
    message: str = ""


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    return platform.system().lower() == "darwin"


def executable_name(base: str) -> str:
    return f"{base}.exe" if is_windows() else base


def bundled_search_roots() -> List[Path]:
    roots: List[Path] = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))

    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        roots.extend(
            [
                executable_dir,
                executable_dir / "_internal",
                executable_dir.parent / "Frameworks",
                executable_dir.parent / "Resources",
            ]
        )

    app_dir = Path(__file__).resolve().parent
    roots.extend(
        [
            app_dir,
            app_dir / "vendor" / "ffmpeg" / "bin",
            app_dir / "vendor" / "ffmpeg" / "windows" / "bin",
            app_dir / "vendor" / "ffmpeg" / "macos" / "bin",
        ]
    )

    unique_roots: List[Path] = []
    seen = set()
    for root in roots:
        try:
            key = root.resolve()
        except OSError:
            key = root
        if key in seen:
            continue
        seen.add(key)
        unique_roots.append(root)
    return unique_roots


def find_executable(base: str, near: Optional[Path] = None) -> Optional[Path]:
    name = executable_name(base)

    if near:
        candidate = near.parent / name
        if candidate.exists():
            return candidate

    for root in bundled_search_roots():
        for candidate in (root / name, root / "bin" / name, root / "ffmpeg" / name):
            if candidate.exists():
                return candidate

    found = shutil.which(name) or shutil.which(base)
    if found:
        return Path(found)

    candidates: List[Path] = []
    if is_windows():
        candidates.extend(
            [
                Path(r"C:\ffmpeg\bin") / name,
                Path(r"C:\Program Files\ffmpeg\bin") / name,
                Path(r"C:\Program Files (x86)\ffmpeg\bin") / name,
            ]
        )
    elif is_macos():
        candidates.extend(
            [
                Path("/opt/homebrew/bin") / name,
                Path("/usr/local/bin") / name,
                Path("/opt/local/bin") / name,
                Path.home() / "homebrew/bin" / name,
            ]
        )
    else:
        candidates.extend(
            [
                Path("/usr/bin") / name,
                Path("/usr/local/bin") / name,
                Path("/snap/bin") / name,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def seconds_from_match(match: re.Match[str]) -> float:
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def format_seconds(value: Optional[float]) -> str:
    if value is None or value < 0 or value == float("inf"):
        return "계산 중"
    total = int(round(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def detect_language() -> str:
    try:
        language = (locale.getlocale()[0] or locale.getdefaultlocale()[0] or "").lower()
    except Exception:
        language = ""
    if language.startswith("ko"):
        return "ko"
    if language.startswith("ja"):
        return "ja"
    return "en"


def shell_join_for_log(cmd: Iterable[str]) -> str:
    return " ".join(quote_for_log(part) for part in cmd)


def quote_for_log(value: str) -> str:
    if not value:
        return '""'
    if re.search(r"\s|[()&|<>^]", value):
        return '"' + value.replace('"', r'\"') + '"'
    return value


def open_path_in_file_manager(path: Path) -> None:
    target = path if path.is_dir() else path.parent
    if is_windows():
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif is_macos():
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def classify_ffmpeg_error(log_text: str) -> str:
    lower = log_text.lower()
    if "moov atom not found" in lower or "invalid data found when processing input" in lower:
        return (
            "이 파일은 정상적인 MP4 구조가 아닐 수 있습니다.\n"
            "다운로드/복사 중 손상되었거나 파일이 완전히 받아지지 않았을 가능성이 큽니다.\n"
            "원본 기기에서 다시 복사해 주세요."
        )
    if (
        "cannot load nvcuda.dll" in lower
        or "no nvenc capable devices found" in lower
        or "unknown encoder 'hevc_nvenc'" in lower
        or "encoder not found" in lower and "hevc_nvenc" in lower
    ):
        return (
            "NVIDIA 하드웨어 인코더를 사용할 수 없습니다.\n"
            "그래픽카드 또는 드라이버가 지원하지 않을 수 있습니다.\n"
            "CPU x265 10-bit 프리셋으로 다시 시도하세요."
        )
    if "unknown encoder 'libx265'" in lower or ("encoder not found" in lower and "libx265" in lower):
        return (
            "현재 ffmpeg에는 libx265 인코더가 포함되어 있지 않습니다.\n"
            "x265 지원 ffmpeg 빌드를 설치해야 합니다."
        )
    if "unknown decoder 'apv" in lower or "codec apv" in lower and "not currently supported" in lower:
        return (
            "현재 ffmpeg가 APV/apv1 입력을 해석하지 못합니다.\n"
            "APV 지원이 포함된 FFmpeg 8.0 이상 빌드를 설치해 주세요."
        )
    return "ffmpeg 변환이 실패했습니다. 로그창의 ffmpeg 메시지를 확인해 주세요."


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.language_code = detect_language()
        self._text_widgets: List[Tuple[tk.Widget, str, str]] = []
        self._language_display_to_code = {name: code for code, name in LANGUAGE_NAMES.items()}
        self.title(self.t("window.title"))
        self.geometry("1120x820")
        self.minsize(980, 720)

        self.files: List[Path] = []
        self.output_paths: Dict[Path, List[Path]] = {}
        self.worker_thread: Optional[threading.Thread] = None
        self.current_process: Optional[subprocess.Popen[str]] = None
        self.process_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.events: "queue.Queue[Tuple[str, object]]" = queue.Queue()
        self.log_lines: List[str] = []
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0

        self._build_variables()
        self._build_ui()
        self._apply_language()
        self._autodetect_ffmpeg()
        self.after(100, self._poll_events)

    def t(self, key: str, **kwargs: object) -> str:
        text = TEXTS.get(self.language_code, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def _message(self, key: str, **kwargs: object) -> str:
        text = MESSAGES.get(self.language_code, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def _register_text(self, widget: tk.Widget, key: str, option: str = "text") -> tk.Widget:
        self._text_widgets.append((widget, option, key))
        widget.configure(**{option: self.t(key)})
        return widget

    def _label_for(self, group: str, key: str) -> str:
        return self.t(f"{group}.{key}")

    def _key_for_label(self, group: str, label: str, keys: Tuple[str, ...], fallback: str) -> str:
        for key in keys:
            if label == self._label_for(group, key):
                return key
        return fallback

    def _build_variables(self) -> None:
        self.encoder_key = ENCODER_CPU
        self.quality_key = QUALITY_RECOMMENDED
        self.resolution_key = RESOLUTION_ORIGINAL
        self.ffmpeg_var = tk.StringVar()
        self.ffprobe_var = tk.StringVar()
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES[self.language_code])
        self.output_mode_var = tk.StringVar(value="source")
        self.output_folder_var = tk.StringVar()
        self.suffix_var = tk.StringVar(value="_ios")
        self.encoder_var = tk.StringVar()
        self.quality_var = tk.StringVar()
        self.resolution_var = tk.StringVar()
        self.keep_hdr_var = tk.BooleanVar(value=True)
        self.make_windows_copy_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.current_file_var = tk.StringVar(value=self.t("status.idle"))
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value=self.t("progress.zero"))
        self.eta_var = tk.StringVar(value=self.t("eta.idle"))
        self.summary_var = tk.StringVar(value=self.t("summary", completed=0, failed=0, skipped=0))
        self.ffmpeg_status_var = tk.StringVar(value=self.t("ffmpeg.before"))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(5, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        title = ttk.Label(header, font=("", 18, "bold"))
        self._register_text(title, "title")
        title.grid(row=0, column=0, sticky="w")

        language_box = ttk.Frame(header)
        language_box.grid(row=0, column=1, sticky="e")
        language_label = ttk.Label(language_box)
        self._register_text(language_label, "language")
        language_label.pack(side="left", padx=(0, 8))
        self.language_combo = ttk.Combobox(
            language_box,
            textvariable=self.language_var,
            values=tuple(LANGUAGE_NAMES.values()),
            state="readonly",
            width=12,
        )
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_language_changed())

        self._build_file_section(root).grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self._build_path_section(root).grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self._build_options_section(root).grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self._build_progress_section(root).grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self._build_log_section(root).grid(row=5, column=0, sticky="nsew")

    def _build_file_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent)
        self._register_text(frame, "section.files")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 6))
        add_files = ttk.Button(buttons, command=self.add_files)
        self._register_text(add_files, "button.add_files")
        add_files.pack(side="left", padx=(0, 6))
        add_folder = ttk.Button(buttons, command=self.add_folder)
        self._register_text(add_folder, "button.add_folder")
        add_folder.pack(side="left", padx=(0, 6))
        remove = ttk.Button(buttons, command=self.remove_selected)
        self._register_text(remove, "button.remove")
        remove.pack(side="left", padx=(0, 6))
        clear = ttk.Button(buttons, command=self.clear_files)
        self._register_text(clear, "button.clear")
        clear.pack(side="left", padx=(0, 6))
        open_selected = ttk.Button(buttons, command=self.open_selected_output)
        self._register_text(open_selected, "button.open_selected")
        open_selected.pack(side="right", padx=(6, 0))

        columns = ("name", "path", "status", "output")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=9)
        self.tree.heading("name", text=self.t("column.name"))
        self.tree.heading("path", text=self.t("column.path"))
        self.tree.heading("status", text=self.t("column.status"))
        self.tree.heading("output", text=self.t("column.output"))
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("path", width=440, anchor="w")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("output", width=260, anchor="w")

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        yscroll.grid(row=1, column=1, sticky="ns", pady=(0, 10), padx=(0, 10))
        xscroll.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        return frame

    def _build_path_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent)
        self._register_text(frame, "section.paths")
        frame.columnconfigure(1, weight=1)

        ffmpeg_label = ttk.Label(frame)
        self._register_text(ffmpeg_label, "label.ffmpeg")
        ffmpeg_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        ttk.Entry(frame, textvariable=self.ffmpeg_var).grid(row=0, column=1, sticky="ew", padx=6, pady=(8, 4))
        choose_ffmpeg = ttk.Button(frame, command=self.choose_ffmpeg)
        self._register_text(choose_ffmpeg, "button.select")
        choose_ffmpeg.grid(row=0, column=2, sticky="e", padx=10, pady=(8, 4))

        ffprobe_label = ttk.Label(frame)
        self._register_text(ffprobe_label, "label.ffprobe")
        ffprobe_label.grid(row=1, column=0, sticky="w", padx=10, pady=4)
        ttk.Entry(frame, textvariable=self.ffprobe_var).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        auto_detect = ttk.Button(frame, command=self.autodetect_ffprobe)
        self._register_text(auto_detect, "button.auto_detect")
        auto_detect.grid(row=1, column=2, sticky="e", padx=10, pady=4)

        ttk.Label(frame, textvariable=self.ffmpeg_status_var, foreground="#555555").grid(
            row=2, column=1, sticky="w", padx=6, pady=(0, 8)
        )

        output_line = ttk.Frame(frame)
        output_line.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 8))
        output_line.columnconfigure(2, weight=1)
        source_radio = ttk.Radiobutton(
            output_line,
            variable=self.output_mode_var,
            value="source",
            command=self.refresh_output_preview,
        )
        self._register_text(source_radio, "radio.source")
        source_radio.grid(row=0, column=0, sticky="w", padx=(0, 12))
        folder_radio = ttk.Radiobutton(
            output_line,
            variable=self.output_mode_var,
            value="folder",
            command=self.refresh_output_preview,
        )
        self._register_text(folder_radio, "radio.folder")
        folder_radio.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ttk.Entry(output_line, textvariable=self.output_folder_var).grid(row=0, column=2, sticky="ew", padx=(0, 6))
        choose_folder = ttk.Button(output_line, command=self.choose_output_folder)
        self._register_text(choose_folder, "button.choose_folder")
        choose_folder.grid(row=0, column=3, sticky="e")
        open_folder = ttk.Button(output_line, command=self.open_output_folder)
        self._register_text(open_folder, "button.open_folder")
        open_folder.grid(row=0, column=4, sticky="e", padx=(6, 0))

        suffix_line = ttk.Frame(frame)
        suffix_line.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        suffix_label = ttk.Label(suffix_line)
        self._register_text(suffix_label, "label.suffix")
        suffix_label.pack(side="left")
        suffix_entry = ttk.Entry(suffix_line, textvariable=self.suffix_var, width=12)
        suffix_entry.pack(side="left", padx=(8, 16))
        suffix_entry.bind("<KeyRelease>", lambda _event: self.refresh_output_preview())
        overwrite = ttk.Checkbutton(suffix_line, variable=self.overwrite_var)
        self._register_text(overwrite, "check.overwrite")
        overwrite.pack(side="left")

        return frame

    def _build_options_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent)
        self._register_text(frame, "section.options")
        for column in range(6):
            frame.columnconfigure(column, weight=1)

        encoder_label = ttk.Label(frame)
        self._register_text(encoder_label, "label.encoder")
        encoder_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        self.encoder_combo = ttk.Combobox(
            frame,
            textvariable=self.encoder_var,
            state="readonly",
        )
        self.encoder_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=6, pady=(8, 4))
        self.encoder_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_encoder_selected())

        quality_label = ttk.Label(frame)
        self._register_text(quality_label, "label.quality")
        quality_label.grid(row=0, column=3, sticky="w", padx=10, pady=(8, 4))
        self.quality_combo = ttk.Combobox(frame, textvariable=self.quality_var, state="readonly")
        self.quality_combo.grid(row=0, column=4, sticky="ew", padx=6, pady=(8, 4))
        self.quality_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_quality_selected())

        resolution_label = ttk.Label(frame)
        self._register_text(resolution_label, "label.resolution")
        resolution_label.grid(row=1, column=0, sticky="w", padx=10, pady=4)
        self.resolution_combo = ttk.Combobox(
            frame,
            textvariable=self.resolution_var,
            state="readonly",
        )
        self.resolution_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=6, pady=4)
        self.resolution_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_resolution_selected())

        self.hdr_check = ttk.Checkbutton(
            frame,
            variable=self.keep_hdr_var,
        )
        self._register_text(self.hdr_check, "check.hdr")
        self.hdr_check.grid(row=1, column=3, columnspan=2, sticky="w", padx=10, pady=4)

        self.windows_copy_check = ttk.Checkbutton(
            frame,
            variable=self.make_windows_copy_var,
            command=self.refresh_output_preview,
        )
        self._register_text(self.windows_copy_check, "check.windows_copy")
        self.windows_copy_check.grid(row=2, column=0, columnspan=6, sticky="w", padx=10, pady=(2, 4))

        self.preset_help = ttk.Label(
            frame,
            foreground="#555555",
        )
        self.preset_help.grid(row=3, column=0, columnspan=6, sticky="w", padx=10, pady=(0, 8))

        return frame

    def _build_progress_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent)
        self._register_text(frame, "section.progress")
        frame.columnconfigure(1, weight=1)

        current_file_label = ttk.Label(frame)
        self._register_text(current_file_label, "label.current_file")
        current_file_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        ttk.Label(frame, textvariable=self.current_file_var).grid(
            row=0, column=1, columnspan=2, sticky="w", padx=6, pady=(8, 4)
        )

        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=4)
        ttk.Label(frame, textvariable=self.progress_text_var, width=10).grid(row=1, column=2, sticky="e", padx=10, pady=4)

        ttk.Label(frame, textvariable=self.eta_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=4)
        ttk.Label(frame, textvariable=self.summary_var).grid(row=2, column=2, sticky="e", padx=10, pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(4, 10))
        self.start_button = ttk.Button(buttons, command=self.start_conversion)
        self._register_text(self.start_button, "button.start")
        self.start_button.pack(side="left", padx=(0, 6))
        self.stop_button = ttk.Button(buttons, command=self.stop_conversion, state="disabled")
        self._register_text(self.stop_button, "button.stop")
        self.stop_button.pack(side="left", padx=(0, 6))
        save_log = ttk.Button(buttons, command=self.save_log)
        self._register_text(save_log, "button.save_log")
        save_log.pack(side="right")

        return frame

    def _build_log_section(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent)
        self._register_text(frame, "section.log")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(frame, height=12, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        return frame

    def _on_language_changed(self) -> None:
        selected = self.language_var.get()
        self.language_code = self._language_display_to_code.get(selected, "en")
        self._apply_language()

    def _apply_language(self) -> None:
        self.title(self.t("window.title"))
        for widget, option, key in self._text_widgets:
            try:
                widget.configure(**{option: self.t(key)})
            except tk.TclError:
                continue

        if hasattr(self, "tree"):
            self.tree.heading("name", text=self.t("column.name"))
            self.tree.heading("path", text=self.t("column.path"))
            self.tree.heading("status", text=self.t("column.status"))
            self.tree.heading("output", text=self.t("column.output"))

        self._sync_option_labels()
        self._update_ffmpeg_status()
        if not (self.worker_thread and self.worker_thread.is_alive()):
            self.current_file_var.set(self.t("status.idle"))
            self.eta_var.set(self.t("eta.idle"))
            self.summary_var.set(self.t("summary", completed=self.completed_count, failed=self.failed_count, skipped=self.skipped_count))
        self.refresh_output_preview()

    def _sync_option_labels(self) -> None:
        if not hasattr(self, "encoder_combo"):
            return
        self.encoder_combo.configure(values=tuple(self._label_for("encoder", key) for key in ENCODER_KEYS))
        self.quality_combo.configure(values=tuple(self._label_for("quality", key) for key in QUALITY_KEYS))
        self.resolution_combo.configure(values=tuple(self._label_for("resolution", key) for key in RESOLUTION_KEYS))
        self.encoder_var.set(self._label_for("encoder", self.encoder_key))
        self.quality_var.set(self._label_for("quality", self.quality_key))
        self.resolution_var.set(self._label_for("resolution", self.resolution_key))
        self._on_encoder_changed()

    def _sync_selected_option_keys(self) -> None:
        self.encoder_key = self._key_for_label("encoder", self.encoder_var.get(), ENCODER_KEYS, self.encoder_key)
        self.quality_key = self._key_for_label("quality", self.quality_var.get(), QUALITY_KEYS, self.quality_key)
        self.resolution_key = self._key_for_label(
            "resolution", self.resolution_var.get(), RESOLUTION_KEYS, self.resolution_key
        )

    def _on_encoder_selected(self) -> None:
        self.encoder_key = self._key_for_label("encoder", self.encoder_var.get(), ENCODER_KEYS, ENCODER_CPU)
        self._on_encoder_changed()
        self.refresh_output_preview()

    def _on_quality_selected(self) -> None:
        self.quality_key = self._key_for_label("quality", self.quality_var.get(), QUALITY_KEYS, QUALITY_RECOMMENDED)

    def _on_resolution_selected(self) -> None:
        self.resolution_key = self._key_for_label(
            "resolution", self.resolution_var.get(), RESOLUTION_KEYS, RESOLUTION_ORIGINAL
        )

    def _autodetect_ffmpeg(self) -> None:
        ffmpeg = find_executable("ffmpeg")
        if ffmpeg:
            self.ffmpeg_var.set(str(ffmpeg))
        self.autodetect_ffprobe()
        self._update_ffmpeg_status()

    def autodetect_ffprobe(self) -> None:
        ffmpeg_path = Path(self.ffmpeg_var.get()) if self.ffmpeg_var.get().strip() else None
        ffprobe = find_executable("ffprobe", near=ffmpeg_path)
        if ffprobe:
            self.ffprobe_var.set(str(ffprobe))
        self._update_ffmpeg_status()

    def choose_ffmpeg(self) -> None:
        filetypes = [("ffmpeg", "ffmpeg.exe" if is_windows() else "ffmpeg"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title=self.t("button.select"), filetypes=filetypes)
        if not path:
            return
        self.ffmpeg_var.set(path)
        self.autodetect_ffprobe()
        self._update_ffmpeg_status()

    def choose_output_folder(self) -> None:
        path = filedialog.askdirectory(title=self.t("button.choose_folder"))
        if not path:
            return
        self.output_folder_var.set(path)
        self.output_mode_var.set("folder")
        self.refresh_output_preview()

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title=self.t("section.files"),
            filetypes=[("Video files", "*.mp4 *.mov *.m4v"), ("All files", "*.*")],
        )
        self._add_paths(Path(path) for path in paths)

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title=self.t("button.add_folder"))
        if not folder:
            return
        folder_path = Path(folder)
        paths = sorted(path for path in folder_path.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS)
        self._add_paths(paths)

    def _add_paths(self, paths: Iterable[Path]) -> None:
        added = 0
        existing = {path.resolve() for path in self.files}
        for path in paths:
            if not path.suffix.lower() in VIDEO_EXTENSIONS:
                continue
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved in existing:
                continue
            self.files.append(resolved)
            existing.add(resolved)
            self.tree.insert(
                "",
                "end",
                iid=str(resolved),
                values=(resolved.name, str(resolved), self.t("status.waiting"), ""),
            )
            added += 1
        if added:
            self.refresh_output_preview()
            self._log(f"[목록] {added}개 파일 추가")

    def remove_selected(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning(APP_NAME, self._message("list_locked"))
            return
        selected = self.tree.selection()
        selected_paths = {Path(iid) for iid in selected}
        self.files = [path for path in self.files if path not in selected_paths]
        for iid in selected:
            self.tree.delete(iid)
        self.refresh_output_preview()

    def clear_files(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showwarning(APP_NAME, self._message("list_locked"))
            return
        self.files.clear()
        self.output_paths.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.progress_var.set(0)
        self.progress_text_var.set(self.t("progress.zero"))
        self.current_file_var.set(self.t("status.idle"))
        self.eta_var.set(self.t("eta.idle"))

    def refresh_output_preview(self) -> None:
        self.output_paths.clear()
        for input_path in self.files:
            output_paths = self._make_output_paths(input_path)
            if output_paths:
                self.output_paths[input_path] = output_paths
            if self.tree.exists(str(input_path)):
                values = list(self.tree.item(str(input_path), "values"))
                while len(values) < 4:
                    values.append("")
                values[3] = self._format_output_paths(output_paths)
                self.tree.item(str(input_path), values=values)

    def _make_output_paths(self, input_path: Path) -> List[Path]:
        output_paths: List[Path] = []
        primary = self._make_output_path(input_path, self.suffix_var.get())
        if primary:
            output_paths.append(primary)
        self._sync_selected_option_keys()
        if self.make_windows_copy_var.get() and self.encoder_key != ENCODER_H264:
            windows = self._make_output_path(input_path, WINDOWS_SUFFIX)
            if windows and windows not in output_paths:
                output_paths.append(windows)
        return output_paths

    def _make_output_path(self, input_path: Path, suffix: str) -> Optional[Path]:
        filename = f"{input_path.stem}{suffix}.mp4"
        if self.output_mode_var.get() == "source":
            return input_path.with_name(filename)
        folder_text = self.output_folder_var.get().strip()
        if not folder_text:
            return None
        return Path(folder_text) / filename

    def _format_output_paths(self, output_paths: List[Path]) -> str:
        return " | ".join(str(path) for path in output_paths)

    def _on_encoder_changed(self) -> None:
        if self.encoder_key == ENCODER_H264:
            self.keep_hdr_var.set(False)
            self.hdr_check.state(["disabled"])
            if hasattr(self, "windows_copy_check"):
                self.make_windows_copy_var.set(False)
                self.windows_copy_check.state(["disabled"])
            self.preset_help.configure(text=self.t("help.h264"))
        else:
            self.hdr_check.state(["!disabled"])
            if hasattr(self, "windows_copy_check"):
                self.windows_copy_check.state(["!disabled"])
            if self.encoder_key == ENCODER_NVENC:
                self.preset_help.configure(text=self.t("help.nvenc"))
            else:
                self.preset_help.configure(text=self.t("help.cpu"))

    def start_conversion(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return

        options = self._read_options()
        if not options:
            return
        if not self.files:
            messagebox.showwarning(APP_NAME, self._message("no_files"))
            return

        self.refresh_output_preview()
        if options.output_mode_source is False and not options.output_folder:
            messagebox.showwarning(APP_NAME, self._message("output_folder_required"))
            return

        version_warning = self._ffmpeg_version_warning(options.ffmpeg_path)
        if version_warning:
            proceed = messagebox.askyesno(APP_NAME, self._message("continue_anyway", warning=version_warning))
            if not proceed:
                return

        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.summary_var.set(self.t("summary", completed=0, failed=0, skipped=0))
        self.stop_event.clear()
        self.progress_var.set(0)
        self.progress_text_var.set(self.t("progress.zero"))
        self.eta_var.set(self.t("eta.calculating"))
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        for input_path in self.files:
            self._set_file_status(input_path, self.t("status.waiting"))

        file_snapshot = list(self.files)
        self.worker_thread = threading.Thread(
            target=self._conversion_worker,
            args=(file_snapshot, options),
            daemon=True,
        )
        self.worker_thread.start()
        self._log("[시작] 변환 작업 시작")

    def _read_options(self) -> Optional[ConversionOptions]:
        self._sync_selected_option_keys()
        ffmpeg_text = self.ffmpeg_var.get().strip()
        if not ffmpeg_text or not Path(ffmpeg_text).exists():
            messagebox.showerror(APP_NAME, self._message("ffmpeg_missing"))
            return None

        ffprobe_text = self.ffprobe_var.get().strip()
        ffprobe_path = Path(ffprobe_text) if ffprobe_text and Path(ffprobe_text).exists() else None

        output_folder: Optional[Path] = None
        output_mode_source = self.output_mode_var.get() == "source"
        if not output_mode_source:
            output_text = self.output_folder_var.get().strip()
            if output_text:
                output_folder = Path(output_text)
                try:
                    output_folder.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    messagebox.showerror(APP_NAME, self._message("output_folder_create_failed", error=exc))
                    return None

        return ConversionOptions(
            ffmpeg_path=Path(ffmpeg_text),
            ffprobe_path=ffprobe_path,
            output_mode_source=output_mode_source,
            output_folder=output_folder,
            suffix=self.suffix_var.get(),
            encoder=self.encoder_key,
            quality=self.quality_key,
            resolution=self.resolution_key,
            keep_hdr_metadata=self.keep_hdr_var.get(),
            make_windows_copy=self.make_windows_copy_var.get(),
            overwrite=self.overwrite_var.get(),
        )

    def _ffmpeg_version_warning(self, ffmpeg_path: Path) -> str:
        try:
            result = subprocess.run(
                [str(ffmpeg_path), "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8,
                check=False,
            )
        except Exception:
            return ""
        first_line = result.stdout.splitlines()[0] if result.stdout else ""
        match = VERSION_RE.search(first_line)
        if not match:
            return ""
        major = int(match.group(1))
        minor = int(match.group(2) or 0)
        if (major, minor) < (8, 0):
            return (
                f"현재 감지된 FFmpeg 버전은 {major}.{minor}입니다.\n"
                "APV/apv1 입력 변환은 FFmpeg 8.0 이상 빌드가 필요할 수 있습니다."
            )
        return ""

    def stop_conversion(self) -> None:
        self.stop_event.set()
        with self.process_lock:
            process = self.current_process
        if process and process.poll() is None:
            try:
                process.terminate()
                self._log("[중지] 현재 ffmpeg 프로세스 종료 요청")
            except OSError as exc:
                self._log(f"[중지] 프로세스 종료 요청 실패: {exc}")
        self.stop_button.configure(state="disabled")

    def _conversion_worker(self, files: List[Path], options: ConversionOptions) -> None:
        results: List[FileResult] = []
        task_plan: List[Tuple[Path, str, Path, ConversionOptions]] = []
        for input_path in files:
            task_plan.extend(self._conversion_tasks_for_file(input_path, options))

        total = len(task_plan)
        for index, (input_path, task_label, output_path, task_options) in enumerate(task_plan, start=1):
            if self.stop_event.is_set():
                break

            self.events.put(("status", (input_path, self.t("status.converting"))))
            self.events.put(("current", f"{input_path.name} - {task_label} ({index}/{total})"))
            self.events.put(("progress", (0.0, self.t("eta.calculating"), "")))
            self.events.put(("log", f"\n[파일] {index}/{total}: {input_path}"))
            self.events.put(("log", f"[출력] {task_label}: {output_path}"))

            if output_path.resolve() == input_path.resolve():
                message = self._message("same_output")
                self.events.put(("status", (input_path, self.t("status.failed"))))
                self.events.put(("log", f"[오류] {message}"))
                results.append(FileResult(input_path, output_path, "failed", message))
                continue

            if output_path.exists() and not task_options.overwrite:
                message = self._message("output_exists")
                self.events.put(("status", (input_path, self.t("status.skipped"))))
                self.events.put(("log", f"[건너뜀] {message}"))
                results.append(FileResult(input_path, output_path, "skipped", message))
                continue

            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                message = f"출력 폴더를 만들 수 없습니다: {exc}"
                self.events.put(("status", (input_path, self.t("status.failed"))))
                self.events.put(("log", f"[오류] {message}"))
                results.append(FileResult(input_path, output_path, "failed", message))
                continue

            duration = self._probe_duration(input_path, task_options.ffprobe_path)
            if duration:
                self.events.put(("log", f"[정보] 영상 길이: {format_seconds(duration)}"))
            else:
                self.events.put(("log", "[정보] ffprobe 길이 확인 실패. ffmpeg 출력에서 길이를 다시 추정합니다."))

            cmd = self._build_ffmpeg_command(input_path, output_path, task_options)
            self.events.put(("log", "[명령어] " + shell_join_for_log(cmd)))

            return_code, log_tail = self._run_ffmpeg(cmd, input_path, duration)

            if self.stop_event.is_set():
                self.events.put(("status", (input_path, self.t("status.stopped"))))
                self.events.put(("log", "[중지] 사용자 요청으로 변환을 중단했습니다."))
                break

            if return_code == 0 and output_path.exists():
                self.events.put(("status", (input_path, self.t("status.completed"))))
                self.events.put(("progress", (100.0, self.t("eta.done"), "")))
                self.events.put(("log", "[완료] 변환 완료"))
                self._verify_output(output_path, task_options.ffprobe_path)
                results.append(FileResult(input_path, output_path, "completed"))
            else:
                friendly = classify_ffmpeg_error(log_tail)
                self.events.put(("status", (input_path, self.t("status.failed"))))
                self.events.put(("log", "[실패] " + friendly.replace("\n", " ")))
                results.append(FileResult(input_path, output_path, "failed", friendly))

        self.events.put(("done", results))

    def _conversion_tasks_for_file(
        self, input_path: Path, options: ConversionOptions
    ) -> List[Tuple[Path, str, Path, ConversionOptions]]:
        tasks = [
            (
                input_path,
                self.t("task.primary"),
                self._worker_output_path(input_path, options),
                options,
            )
        ]
        if options.make_windows_copy and options.encoder != ENCODER_H264:
            windows_options = replace(options, suffix=WINDOWS_SUFFIX, encoder=ENCODER_H264, keep_hdr_metadata=False)
            tasks.append(
                (
                    input_path,
                    self.t("task.windows"),
                    self._worker_output_path(input_path, windows_options),
                    windows_options,
                )
            )
        return tasks

    def _worker_output_path(self, input_path: Path, options: ConversionOptions) -> Path:
        filename = f"{input_path.stem}{options.suffix}.mp4"
        if options.output_mode_source:
            return input_path.with_name(filename)
        assert options.output_folder is not None
        return options.output_folder / filename

    def _probe_duration(self, input_path: Path, ffprobe_path: Optional[Path]) -> Optional[float]:
        if not ffprobe_path:
            return None
        cmd = [
            str(ffprobe_path),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
            return float(result.stdout.strip())
        except Exception:
            return None

    def _build_ffmpeg_command(self, input_path: Path, output_path: Path, options: ConversionOptions) -> List[str]:
        cmd = [
            str(options.ffmpeg_path),
            "-hide_banner",
            "-nostdin",
            "-y" if options.overwrite else "-n",
            "-progress",
            "pipe:1",
            "-nostats",
            "-fflags",
            "+genpts",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
        ]

        video_filters: List[str] = []
        if options.resolution == RESOLUTION_1080P:
            video_filters.append("scale=1920:-2")
        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])

        if options.encoder == ENCODER_NVENC:
            quality = NVENC_QUALITY[options.quality]
            cmd.extend(
                [
                    "-c:v",
                    "hevc_nvenc",
                    "-profile:v",
                    "main10",
                    "-pix_fmt",
                    "p010le",
                    "-b:v",
                    quality["b:v"],
                    "-maxrate",
                    quality["maxrate"],
                    "-bufsize",
                    quality["bufsize"],
                    "-tag:v",
                    "hvc1",
                ]
            )
            if options.keep_hdr_metadata:
                cmd.extend(["-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"])
        elif options.encoder == ENCODER_H264:
            quality = CPU_QUALITY[options.quality]
            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    quality["preset"],
                    "-crf",
                    quality["crf"],
                    "-pix_fmt",
                    "yuv420p",
                    "-color_primaries",
                    "bt709",
                    "-color_trc",
                    "bt709",
                    "-colorspace",
                    "bt709",
                    "-x264-params",
                    "colorprim=bt709:transfer=bt709:colormatrix=bt709",
                ]
            )
        else:
            quality = CPU_QUALITY[options.quality]
            cmd.extend(
                [
                    "-c:v",
                    "libx265",
                    "-preset",
                    quality["preset"],
                    "-crf",
                    quality["crf"],
                    "-pix_fmt",
                    "yuv420p10le",
                    "-tag:v",
                    "hvc1",
                ]
            )
            if options.keep_hdr_metadata:
                cmd.extend(
                    [
                        "-color_primaries",
                        "bt2020",
                        "-color_trc",
                        "arib-std-b67",
                        "-colorspace",
                        "bt2020nc",
                        "-x265-params",
                        "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
                    ]
                )

        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output_path)])
        return cmd

    def _run_ffmpeg(self, cmd: List[str], input_path: Path, duration: Optional[float]) -> Tuple[int, str]:
        started_at = time.monotonic()
        tail_lines: List[str] = []
        inferred_duration = duration

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            text = f"ffmpeg 실행 실패: {exc}"
            self.events.put(("log", f"[오류] {text}"))
            return 1, text

        with self.process_lock:
            self.current_process = process

        assert process.stdout is not None
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue
            tail_lines.append(line)
            tail_lines = tail_lines[-80:]

            duration_match = DURATION_RE.search(line)
            if duration_match and not inferred_duration:
                inferred_duration = seconds_from_match(duration_match)

            current_seconds = self._extract_progress_seconds(line)
            if current_seconds is not None and inferred_duration and inferred_duration > 0:
                percent = min(100.0, max(0.0, current_seconds / inferred_duration * 100.0))
                eta = self._estimate_eta(started_at, percent)
                speed = self._extract_speed(line)
                eta_text = self.t("eta.remaining", time=format_seconds(eta)) if eta is not None else self.t("eta.calculating")
                self.events.put(("progress", (percent, eta_text, speed)))

            if not self._is_progress_noise(line):
                self.events.put(("log", line))

            if self.stop_event.is_set() and process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass

        return_code = process.wait()
        with self.process_lock:
            if self.current_process is process:
                self.current_process = None
        return return_code, "\n".join(tail_lines)

    def _extract_progress_seconds(self, line: str) -> Optional[float]:
        for regex in (OUT_TIME_RE, TIME_RE):
            match = regex.search(line)
            if match:
                return seconds_from_match(match)
        if line.startswith("out_time_ms=") or line.startswith("out_time_us="):
            try:
                return int(line.split("=", 1)[1]) / 1_000_000.0
            except ValueError:
                return None
        return None

    def _extract_speed(self, line: str) -> str:
        if line.startswith("speed="):
            return line.split("=", 1)[1].strip()
        match = SPEED_RE.search(line)
        return match.group(1) if match else ""

    def _estimate_eta(self, started_at: float, percent: float) -> Optional[float]:
        if percent <= 0.1:
            return None
        elapsed = time.monotonic() - started_at
        total_estimate = elapsed / (percent / 100.0)
        return max(0.0, total_estimate - elapsed)

    def _is_progress_noise(self, line: str) -> bool:
        return (
            line.startswith("frame=")
            or line.startswith("fps=")
            or line.startswith("stream_")
            or line.startswith("total_size=")
            or line.startswith("out_time")
            or line.startswith("dup_frames=")
            or line.startswith("drop_frames=")
            or line.startswith("speed=")
            or line.startswith("progress=")
            or line.startswith("bitrate=")
        )

    def _verify_output(self, output_path: Path, ffprobe_path: Optional[Path]) -> None:
        if not ffprobe_path:
            self.events.put(("log", "[검증] ffprobe가 없어 출력 검증을 건너뜁니다."))
            return
        cmd = [
            str(ffprobe_path),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,codec_tag_string,pix_fmt,color_primaries,color_transfer,color_space:format=format_name,duration",
            "-of",
            "default=noprint_wrappers=1",
            str(output_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except Exception as exc:
            self.events.put(("log", f"[검증] 실패: {exc}"))
            return
        if result.returncode != 0:
            self.events.put(("log", "[검증] ffprobe 검증 실패: " + result.stderr.strip()))
            return
        for line in result.stdout.splitlines():
            if line.strip():
                self.events.put(("log", "[검증] " + line.strip()))
        self.events.put(("log", "[검증] 완료"))

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "log":
                    self._log(str(payload))
                elif event == "status":
                    input_path, status = payload  # type: ignore[misc]
                    self._set_file_status(input_path, status)
                elif event == "current":
                    self.current_file_var.set(str(payload))
                elif event == "progress":
                    percent, eta, speed = payload  # type: ignore[misc]
                    self.progress_var.set(float(percent))
                    self.progress_text_var.set(f"{float(percent):.1f}%")
                    suffix = f" / {self.t('speed')}: {speed}" if speed else ""
                    self.eta_var.set(str(eta) + suffix)
                elif event == "done":
                    self._handle_done(payload)  # type: ignore[arg-type]
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _handle_done(self, results: List[FileResult]) -> None:
        self.completed_count = sum(1 for result in results if result.status == "completed")
        self.failed_count = sum(1 for result in results if result.status == "failed")
        self.skipped_count = sum(1 for result in results if result.status == "skipped")
        self.summary_var.set(
            self.t("summary", completed=self.completed_count, failed=self.failed_count, skipped=self.skipped_count)
        )
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if self.stop_event.is_set():
            self.current_file_var.set(self.t("status.user_stopped"))
            self._log("[요약] 사용자 요청으로 작업이 중지되었습니다.")
        else:
            self.current_file_var.set(self.t("status.done"))
            self.progress_var.set(100 if self.completed_count else self.progress_var.get())
            self._log(
                f"[요약] 완료 {self.completed_count}개, 실패 {self.failed_count}개, 건너뜀 {self.skipped_count}개"
            )
            if self.failed_count:
                first_failure = next((result for result in results if result.status == "failed"), None)
                if first_failure:
                    messagebox.showwarning(APP_NAME, first_failure.message)
            else:
                messagebox.showinfo(APP_NAME, self._message("done"))

    def _set_file_status(self, input_path: Path, status: str) -> None:
        iid = str(input_path)
        if not self.tree.exists(iid):
            return
        values = list(self.tree.item(iid, "values"))
        while len(values) < 4:
            values.append("")
        values[2] = status
        self.tree.item(iid, values=values)

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_lines.append(line)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def save_log(self) -> None:
        default = "conversion_log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        path = filedialog.asksaveasfilename(
            title=self.t("button.save_log"),
            defaultextension=".txt",
            initialfile=default,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            Path(path).write_text("\n".join(self.log_lines) + "\n", encoding="utf-8")
            messagebox.showinfo(APP_NAME, self._message("log_saved"))
        except OSError as exc:
            messagebox.showerror(APP_NAME, self._message("log_save_failed", error=exc))

    def open_output_folder(self) -> None:
        if self.output_mode_var.get() == "folder" and self.output_folder_var.get().strip():
            target = Path(self.output_folder_var.get().strip())
        elif self.files:
            target = self.files[0].parent
        else:
            messagebox.showinfo(APP_NAME, self._message("open_folder_none"))
            return
        try:
            open_path_in_file_manager(target)
        except Exception as exc:
            messagebox.showerror(APP_NAME, self._message("open_folder_failed", error=exc))

    def open_selected_output(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, self._message("select_file_first"))
            return
        input_path = Path(selected[0])
        outputs = self.output_paths.get(input_path, [])
        output = outputs[0] if outputs else None
        if not output:
            messagebox.showinfo(APP_NAME, self._message("no_output_path"))
            return
        try:
            open_path_in_file_manager(output)
        except Exception as exc:
            messagebox.showerror(APP_NAME, self._message("open_output_failed", error=exc))

    def _update_ffmpeg_status(self) -> None:
        ffmpeg = self.ffmpeg_var.get().strip()
        ffprobe = self.ffprobe_var.get().strip()
        if not ffmpeg:
            self.ffmpeg_status_var.set(self.t("ffmpeg.missing"))
            return
        status = self.t("ffmpeg.detected")
        if ffprobe:
            status += " / " + self.t("ffprobe.detected")
        else:
            status += " / " + self.t("ffprobe.missing")
        status += " / " + self.t("ffmpeg.apv")
        self.ffmpeg_status_var.set(status)


def main() -> int:
    app = ConverterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
