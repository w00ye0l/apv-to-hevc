# S26 APV to iPhone Converter

Samsung S26 APV/apv1 영상 파일을 iPhone, QuickTime, iCloud, KakaoTalk에서 재생하기 쉬운 MP4로 변환하는 Python tkinter GUI 앱입니다.

## 지원 환경

- Windows 10 이상
- macOS 12 이상 권장
- Python 3.9 이상
- FFmpeg 필요
- APV/apv1 입력 변환은 FFmpeg 8.0 이상 빌드 권장

## 실행

```bash
python s26_apv_iphone_converter.py
```

macOS에서 `python`이 Python 2로 잡히면 다음처럼 실행하세요.

```bash
python3 s26_apv_iphone_converter.py
```

## FFmpeg 설치

### Windows

1. FFmpeg Windows 빌드를 내려받습니다.
2. 예: `C:\ffmpeg\bin\ffmpeg.exe` 위치에 둡니다.
3. 앱 실행 후 자동 감지되지 않으면 `ffmpeg` 선택 버튼으로 직접 지정합니다.

### macOS

Homebrew 사용 시:

```bash
brew install ffmpeg
```

일반 경로 `/opt/homebrew/bin/ffmpeg`, `/usr/local/bin/ffmpeg`는 앱에서 자동 탐색합니다.

## 사용 방법

1. 앱을 실행합니다.
2. `파일 추가` 또는 `폴더 추가`로 MP4/MOV/M4V 파일을 추가합니다.
3. 출력 위치를 원본 폴더 또는 별도 출력 폴더로 선택합니다.
4. 기본값인 `CPU x265 10-bit / 고화질 권장 / 원본 해상도 유지`를 사용하거나 원하는 프리셋을 고릅니다.
5. `변환 시작`을 누릅니다.
6. 변환 완료 후 `출력 폴더 열기` 또는 `선택 출력 위치 열기`로 결과 파일 위치를 엽니다.

변환된 파일은 기본적으로 다음 이름으로 저장됩니다.

```text
원본파일명_ios.mp4
```

## 주요 기능

- Windows/macOS 공용 tkinter GUI
- ffmpeg/ffprobe 자동 탐색
- 여러 파일 순차 변환
- 진행률 표시
- 예상 남은 시간 표시
- 변환 로그 표시 및 저장
- 중지 버튼
- CPU x265 10-bit HEVC 프리셋
- NVIDIA NVENC 10-bit HEVC 프리셋
- H.264 SDR 호환 프리셋
- 원본 해상도 유지 또는 1080p 축소
- HEVC 출력에 `hvc1` 태그 적용
- 오디오는 AAC 192k로 변환
- 오디오 없는 파일도 처리

## 패키징

패키징은 선택 사항입니다. PyInstaller가 필요합니다.

Windows:

```bat
build_windows_exe.bat
```

결과물은 보통 `dist\S26 APV to iPhone Converter.exe`에 생성됩니다.

macOS:

```bash
chmod +x build_macos_app.sh
./build_macos_app.sh
```

결과물은 `dist/S26 APV to iPhone Converter.app`에 생성됩니다.

패키징된 앱도 FFmpeg 실행 파일이 필요합니다. 사용자의 PATH에 있거나 GUI에서 직접 선택할 수 있어야 합니다.

## GitHub Actions 자동 빌드

`.github/workflows/build-release.yml`이 포함되어 있습니다.

- Pull request: Windows/macOS 빌드가 되는지 확인하고 artifact를 올립니다.
- 수동 실행: GitHub Actions 화면에서 `Build Desktop Apps`를 선택해 실행할 수 있습니다.
- 태그 배포: `v1.0.0` 같은 태그를 push하면 GitHub Release가 생성되고 Windows/macOS zip 파일이 업로드됩니다.

예:

```bash
git tag v1.0.0
git push origin v1.0.0
```

고객용 사이트에는 다음 형식의 링크를 버튼으로 연결하면 됩니다.

```text
https://github.com/w00ye0l/apv-to-hevc/releases/latest/download/S26_APV_to_iPhone_Converter_Windows.zip
https://github.com/w00ye0l/apv-to-hevc/releases/latest/download/S26_APV_to_iPhone_Converter_macOS.zip
```

`site/download.html`에 다운로드 페이지 예시가 들어 있습니다. 사이트에 맞게 복사해서 붙이면 됩니다.
