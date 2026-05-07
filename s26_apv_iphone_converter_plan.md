# S26 APV → iPhone HEVC 변환 GUI 기획 문서

## 1. 프로젝트 목적

삼성 S26에서 촬영한 `apv1 / APV` 코덱 기반 MP4 동영상이 아이폰, QuickTime, iCloud, 카카오톡 등에서 정상 재생되지 않는 문제를 해결하기 위해, 사용자가 GUI에서 파일을 선택하고 버튼 한 번으로 아이폰 호환 MP4로 변환할 수 있는 Windows용 프로그램을 만든다.

핵심 목표는 다음과 같다.

- 원본 프레임 유지
- 원본 해상도 유지 옵션 제공
- HDR/HLG 최대한 유지
- 아이폰 호환 HEVC MP4 출력
- 여러 파일 일괄 변환 지원
- ffmpeg 명령어를 모르는 사용자도 사용 가능하게 GUI화

---

## 2. 대상 사용자

비개발자 사용자가 주요 대상이다.

사용자는 다음 정도만 할 수 있다고 가정한다.

- 파일 선택
- 폴더 선택
- 버튼 클릭
- 변환 완료 파일 확인

터미널 명령어 입력, 환경변수 설정, ffmpeg 옵션 이해는 요구하지 않는다.

---

## 3. 실행 환경

### 필수 환경

- Windows 10 이상
- Python 3.10 이상
- `ffmpeg.exe` 필요

### ffmpeg 처리 방식

앱은 다음 방식으로 ffmpeg를 찾는다.

1. 시스템 PATH에서 `ffmpeg` 검색
2. 일반적인 설치 경로 검색
   - `C:\ffmpeg\bin\ffmpeg.exe`
   - `C:\Program Files\ffmpeg\bin\ffmpeg.exe`
3. 사용자가 GUI에서 직접 `ffmpeg.exe` 선택 가능

`ffprobe.exe`도 가능하면 같은 폴더에서 자동 탐색한다.

---

## 4. 기술 스택

### 1차 구현

- Python
- tkinter
- subprocess
- threading
- queue
- pathlib
- re
- shutil

외부 GUI 라이브러리는 쓰지 않는다.  
즉, `pip install` 없이 Python 기본 라이브러리만으로 실행 가능하게 만든다.

### 선택 사항

나중에 배포용 exe가 필요하면 PyInstaller 사용 가능.

```bash
pyinstaller --onefile --windowed app.py
```

---

## 5. 핵심 기능

### 5.1 파일 선택

사용자는 GUI에서 다음을 할 수 있어야 한다.

- MP4/MOV/M4V 파일 여러 개 선택
- 폴더 선택 후 해당 폴더의 MP4/MOV/M4V 전체 추가
- 선택 파일 제거
- 전체 목록 비우기

파일 목록은 Listbox 또는 Treeview로 보여준다.

표시 항목:

- 파일명
- 전체 경로
- 변환 상태: 대기 / 변환 중 / 완료 / 실패 / 건너뜀

---

### 5.2 출력 위치

사용자는 출력 위치를 선택할 수 있어야 한다.

옵션:

- 원본 파일과 같은 폴더에 저장
- 별도 출력 폴더 지정

기본 출력 파일명 규칙:

```text
원본파일명_ios.mp4
```

예:

```text
20260412_190853.mp4
→ 20260412_190853_ios.mp4
```

동일한 출력 파일이 이미 존재할 경우:

- 기본값: 덮어쓰지 않고 건너뜀
- 옵션: “기존 파일 덮어쓰기” 체크박스 제공

---

### 5.3 변환 프리셋

앱은 최소 3개 프리셋을 제공한다.

---

#### 프리셋 A: 화질 우선 / CPU x265 10-bit

기본 추천 프리셋이다.

목표:

- 프레임 유지
- HDR/HLG 유지
- 고화질 유지
- 아이폰 호환

ffmpeg 옵션 핵심:

```bash
-c:v libx265
-pix_fmt yuv420p10le
-tag:v hvc1
-c:a aac
-movflags +faststart
```

권장 명령어 형태:

```bash
ffmpeg -fflags +genpts -i input.mp4 ^
-map 0:v:0 -map 0:a:0? ^
-c:v libx265 -preset medium -crf 20 ^
-pix_fmt yuv420p10le ^
-tag:v hvc1 ^
-color_primaries bt2020 ^
-color_trc arib-std-b67 ^
-colorspace bt2020nc ^
-c:a aac -b:a 192k ^
-movflags +faststart ^
output_ios.mp4
```

주의:

- FPS 옵션은 넣지 않는다.
- `fps=30` 같은 강제 프레임 변경 금지.
- 해상도도 기본값은 원본 유지.

---

#### 프리셋 B: 속도 우선 / NVIDIA NVENC 10-bit

NVIDIA GPU가 있는 윈도우 PC용.

목표:

- 빠른 변환
- HDR/10-bit 유지
- 아이폰 호환
- CPU 부담 감소

ffmpeg 옵션 핵심:

```bash
-c:v hevc_nvenc
-profile:v main10
-pix_fmt p010le
-tag:v hvc1
```

권장 명령어 형태:

```bash
ffmpeg -fflags +genpts -i input.mp4 ^
-map 0:v:0 -map 0:a:0? ^
-c:v hevc_nvenc ^
-profile:v main10 ^
-pix_fmt p010le ^
-b:v 18M ^
-maxrate 30M ^
-bufsize 36M ^
-tag:v hvc1 ^
-color_primaries bt2020 ^
-color_trc arib-std-b67 ^
-colorspace bt2020nc ^
-c:a aac -b:a 192k ^
-movflags +faststart ^
output_ios.mp4
```

화질 옵션별 비트레이트:

| 품질 | b:v | maxrate | bufsize |
|---|---:|---:|---:|
| 원본급 | 28M | 45M | 56M |
| 고화질 권장 | 18M | 30M | 36M |
| 균형 | 12M | 20M | 24M |
| 용량 절약 | 8M | 14M | 16M |

---

#### 프리셋 C: 최후 호환용 / H.264 SDR

HDR 유지가 목적이 아니라, 정말 재생 호환만 필요할 때 쓰는 옵션이다.

목표:

- 모든 기기에서 재생 가능
- HDR은 포기
- 색상은 SDR BT.709로 변환

명령어 형태:

```bash
ffmpeg -fflags +genpts -i input.mp4 ^
-map 0:v:0 -map 0:a:0? ^
-c:v libx264 -preset medium -crf 20 ^
-pix_fmt yuv420p ^
-color_primaries bt709 ^
-color_trc bt709 ^
-colorspace bt709 ^
-c:a aac -b:a 192k ^
-movflags +faststart ^
output_ios.mp4
```

이 프리셋은 “아이폰 호환은 되지만 S26로 찍은 HDR 느낌은 줄어들 수 있음”이라고 UI에 안내한다.

---

### 5.4 화질 옵션

GUI에는 다음 품질 옵션을 둔다.

#### CPU x265 기준

| 옵션 | CRF | Preset | 설명 |
|---|---:|---|---|
| 원본급 | 18 | slow | 용량 큼, 화질 최우선 |
| 고화질 권장 | 20 | medium | 추천값 |
| 균형 | 23 | medium | 적당한 용량 |
| 용량 절약 | 26 | fast | 공유용 |

#### H.264 기준

| 옵션 | CRF | Preset |
|---|---:|---|
| 원본급 | 18 | slow |
| 고화질 권장 | 20 | medium |
| 균형 | 23 | medium |
| 용량 절약 | 26 | fast |

#### NVENC 기준

CRF가 아니라 비트레이트 기반으로 처리한다.

| 옵션 | b:v |
|---|---:|
| 원본급 | 28M |
| 고화질 권장 | 18M |
| 균형 | 12M |
| 용량 절약 | 8M |

---

### 5.5 해상도 옵션

GUI에서 해상도 옵션을 제공한다.

1. 원본 해상도 유지
   - 기본값
   - S26 촬영 품질 유지 목적

2. 1080p로 줄이기
   - 용량 절약 목적
   - 필터 사용:

```bash
-vf scale=1920:-2
```

주의:

- 프레임은 어떤 경우에도 기본적으로 건드리지 않는다.
- `fps=30` 강제 옵션은 넣지 않는다.

---

### 5.6 오디오 처리

원본 오디오가 Linear PCM이면 용량이 커지므로 AAC로 변환한다.

기본값:

```bash
-c:a aac -b:a 192k
```

오디오 스트림이 없는 파일도 처리할 수 있게 한다.

따라서 map 옵션은 다음처럼 사용한다.

```bash
-map 0:v:0 -map 0:a:0?
```

`?`를 붙여 오디오가 없어도 에러가 나지 않게 한다.

---

### 5.7 진행률 표시

ffmpeg는 stdout/stderr에 진행 정보를 출력한다.

앱은 ffmpeg 출력 중 다음 패턴을 파싱한다.

```text
time=00:01:23.45
```

전체 길이는 ffprobe로 가져온다.

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
```

진행률 계산:

```text
현재 변환 시간 / 전체 영상 길이 * 100
```

GUI 표시:

- 현재 변환 중인 파일명
- 전체 파일 중 몇 번째인지
- 개별 파일 진행률
- 로그창
- 완료/실패 개수

---

### 5.8 변환 방식

여러 파일은 병렬이 아니라 순차 처리한다.

이유:

- CPU/GPU 과부하 방지
- 발열 방지
- 실패 원인 추적 용이
- 일반 사용자에게 안정적

처리 흐름:

```text
파일 1 변환
→ 완료/실패 기록
→ 파일 2 변환
→ 완료/실패 기록
→ ...
→ 전체 요약 표시
```

---

### 5.9 중지 기능

“중지” 버튼을 제공한다.

동작:

- 현재 실행 중인 ffmpeg 프로세스 terminate
- 남은 파일은 변환하지 않음
- 로그에 “사용자 중지” 기록
- 이미 완료된 출력 파일은 유지

---

### 5.10 로그 기능

로그창에는 다음을 표시한다.

- 시작 파일명
- 출력 파일명
- 실제 실행한 ffmpeg 명령어
- ffmpeg 출력 일부
- 오류 메시지
- 완료/실패 요약

추가로 “로그 저장” 버튼이 있으면 좋다.

로그 저장 파일 예:

```text
conversion_log_YYYYMMDD_HHMMSS.txt
```

---

## 6. 에러 처리

다음 에러는 사용자에게 알기 쉽게 표시한다.

---

### 6.1 ffmpeg 없음

조건:

- ffmpeg 경로가 비어 있음
- 파일이 존재하지 않음

메시지:

```text
ffmpeg.exe를 찾을 수 없습니다.
ffmpeg.exe 위치를 선택하세요.
예: C:\ffmpeg\bin\ffmpeg.exe
```

---

### 6.2 입력 파일 손상

ffmpeg 로그에 다음이 포함될 경우:

```text
moov atom not found
Invalid data found when processing input
```

사용자 메시지:

```text
이 파일은 정상적인 MP4 구조가 아닐 수 있습니다.
다운로드/복사 중 손상되었거나 파일이 완전히 받아지지 않았을 가능성이 큽니다.
원본 기기에서 다시 복사해 주세요.
```

---

### 6.3 출력 파일 이미 존재

덮어쓰기 옵션이 꺼져 있으면 건너뜀.

메시지:

```text
출력 파일이 이미 존재하여 건너뜁니다.
덮어쓰려면 '기존 파일 덮어쓰기'를 체크하세요.
```

---

### 6.4 NVENC 사용 불가

NVIDIA 프리셋 사용 중 다음이 발생할 수 있음.

```text
Cannot load nvcuda.dll
No NVENC capable devices found
Unknown encoder 'hevc_nvenc'
```

사용자 메시지:

```text
NVIDIA 하드웨어 인코더를 사용할 수 없습니다.
그래픽카드 또는 드라이버가 지원하지 않을 수 있습니다.
CPU x265 10-bit 프리셋으로 다시 시도하세요.
```

---

### 6.5 libx265 없음

ffmpeg 빌드에 x265가 없으면:

```text
Unknown encoder 'libx265'
```

사용자 메시지:

```text
현재 ffmpeg에는 libx265 인코더가 포함되어 있지 않습니다.
x265 지원 ffmpeg 빌드를 설치해야 합니다.
```

---

## 7. UI 구성

메인 화면 구성은 다음과 같다.

```text
[앱 제목]
S26 APV → iPhone HEVC 변환기

1) ffmpeg.exe 위치
[경로 입력창] [ffmpeg.exe 선택]

2) 변환할 영상 파일
[파일 추가] [폴더 추가] [선택 제거] [전체 비우기]
[파일 목록]

3) 출력 위치
[출력 폴더 입력창] [출력 폴더 선택]
[ ] 원본 폴더에 저장
접미사: [_ios]

4) 변환 옵션
인코더:
  - CPU x265 10-bit / 화질 우선
  - NVIDIA NVENC 10-bit / 속도 우선
  - H.264 SDR / 최후 호환용

화질:
  - 원본급
  - 고화질 권장
  - 균형
  - 용량 절약

해상도:
  - 원본 해상도 유지
  - 1080p로 줄이기

[✓] BT.2020 HLG HDR 메타데이터 유지
[ ] 기존 출력 파일 덮어쓰기

[변환 시작] [중지]

현재 파일:
진행률 바:
로그창:
```

---

## 8. 기본값

앱 실행 시 기본값은 다음으로 한다.

```text
인코더: CPU x265 10-bit / 화질 우선
화질: 고화질 권장
해상도: 원본 해상도 유지
HDR 메타데이터 유지: 체크
출력 위치: 원본 파일과 같은 폴더
접미사: _ios
덮어쓰기: 꺼짐
```

이 기본값은 “삼성 S26로 찍은 이유가 화질/프레임/HDR 때문”이라는 사용 목적에 맞춘다.

---

## 9. 구현상 중요한 규칙

### 9.1 subprocess는 shell=True 쓰지 말 것

파일 경로에 공백, 한글, 특수문자가 있어도 안정적으로 동작하게 하려면 명령어 문자열이 아니라 리스트로 실행한다.

예:

```python
cmd = [
    ffmpeg_path,
    "-fflags", "+genpts",
    "-i", str(input_path),
    "-map", "0:v:0",
    "-map", "0:a:0?",
    "-c:v", "libx265",
    "-preset", "medium",
    "-crf", "20",
    "-pix_fmt", "yuv420p10le",
    "-tag:v", "hvc1",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    str(output_path),
]

subprocess.Popen(cmd, ...)
```

---

### 9.2 GUI 프리징 방지

변환은 반드시 별도 thread에서 실행한다.

tkinter 메인 스레드에서 ffmpeg를 직접 실행하면 UI가 멈춘다.

권장 구조:

```text
Main Thread:
  - GUI
  - 버튼 이벤트
  - queue polling

Worker Thread:
  - ffmpeg 실행
  - 로그 queue에 전달
  - 진행률 queue에 전달
```

---

### 9.3 FPS 유지

기본 변환 명령어에 다음을 넣지 않는다.

```bash
-r 30
-vf fps=30
```

프레임은 원본 그대로 유지해야 한다.

---

### 9.4 아이폰 호환 태그

HEVC 출력에는 반드시 다음을 넣는다.

```bash
-tag:v hvc1
```

이 옵션이 없으면 일부 Apple 기기/QuickTime에서 HEVC 파일 인식이 불안정할 수 있다.

---

### 9.5 HDR 유지

HDR/HLG 유지 목적이면 다음 메타데이터를 넣는다.

```bash
-color_primaries bt2020
-color_trc arib-std-b67
-colorspace bt2020nc
```

픽셀 포맷은 CPU x265 기준:

```bash
-pix_fmt yuv420p10le
```

NVENC 기준:

```bash
-pix_fmt p010le
```

---

## 10. 출력 파일 검증 기능

가능하면 변환 후 ffprobe로 출력 파일 정보를 확인한다.

확인 항목:

- video codec: `hevc`
- audio codec: `aac`
- pixel format: `yuv420p10le` 또는 `p010le`
- container: mp4
- duration 존재 여부

검증 실패 시 로그에 경고 표시.

예:

```text
[검증] 비디오 코덱: hevc
[검증] 오디오 코덱: aac
[검증] 픽셀 포맷: yuv420p10le
[검증] 완료
```

---

## 11. 향후 확장 기능

1차 버전에서는 필수가 아니지만, 나중에 추가할 수 있다.

- 드래그 앤 드롭 지원
- 변환 완료 후 출력 폴더 열기
- 변환 전 원본 정보 표시
- 변환 후 용량 비교
- Intel Quick Sync HEVC 지원
- AMD AMF HEVC 지원
- PyInstaller로 exe 패키징
- 프리셋 저장/불러오기
- 실패 파일만 다시 변환
- 로그 파일 자동 저장

---

## 12. 최종 산출물

Codex가 만들어야 하는 파일:

```text
s26_apv_iphone_converter.py
README.md
requirements.txt
```

`requirements.txt`는 기본적으로 비워두거나 다음처럼 작성한다.

```text
# No external dependencies required.
```

선택적으로 exe 빌드 스크립트:

```text
build_exe.bat
```

내용:

```bat
pyinstaller --onefile --windowed s26_apv_iphone_converter.py
```

---

## 13. Codex에게 줄 최종 구현 지시문

아래 문장을 그대로 Codex에게 전달하면 된다.

```text
위 기획 문서를 기준으로 Windows용 Python tkinter GUI 앱을 구현해줘.

앱 이름은 "S26 APV to iPhone Converter"로 해줘.

핵심 요구사항:
1. ffmpeg.exe 경로를 자동 탐색하고, 사용자가 직접 선택할 수도 있게 해줘.
2. MP4/MOV/M4V 파일 여러 개를 선택해서 목록에 추가할 수 있게 해줘.
3. 폴더 선택 시 해당 폴더의 MP4/MOV/M4V 파일을 자동 추가하게 해줘.
4. 출력 위치는 원본 폴더 또는 별도 출력 폴더를 선택할 수 있게 해줘.
5. 기본 출력 파일명은 원본파일명_ios.mp4로 해줘.
6. 변환은 순차 처리해줘.
7. 변환 중 GUI가 멈추지 않도록 threading과 queue를 사용해줘.
8. ffmpeg 진행 로그에서 time= 값을 파싱해서 progress bar를 업데이트해줘.
9. ffprobe가 있으면 duration을 읽어서 진행률을 계산해줘.
10. 기본 프리셋은 CPU x265 10-bit / 고화질 권장 / 원본 해상도 유지 / HDR 메타데이터 유지로 해줘.
11. 프레임은 원본 그대로 유지하고, -r 30 또는 fps=30 같은 강제 프레임 옵션은 넣지 마.
12. HEVC 출력에는 -tag:v hvc1 옵션을 반드시 넣어줘.
13. 오디오는 AAC 192k로 변환해줘.
14. 입력 파일에 오디오가 없어도 실패하지 않도록 -map 0:a:0? 를 사용해줘.
15. NVIDIA NVENC 10-bit 프리셋도 제공해줘.
16. H.264 SDR 최후 호환용 프리셋도 제공해줘.
17. 변환 실패 시 moov atom not found, NVENC 없음, libx265 없음 같은 주요 오류를 사용자 친화적인 메시지로 보여줘.
18. subprocess 실행 시 shell=True를 쓰지 말고 리스트 인자로 실행해줘.
19. 한글 경로와 공백 있는 파일 경로가 정상 동작하게 해줘.
20. 코드 전체를 하나의 Python 파일로 완성해줘.
```

---

## 14. 개발 완료 기준

다음 테스트를 통과하면 1차 버전 완료로 본다.

- 파일 하나 선택 후 변환 가능
- 파일 여러 개 선택 후 순차 변환 가능
- 원본 파일명에 한글/공백이 있어도 변환 가능
- 출력 파일명이 `_ios.mp4`로 생성됨
- CPU x265 프리셋 동작
- NVIDIA 없는 PC에서 NVENC 선택 시 친절한 오류 표시
- 변환 중 GUI 멈추지 않음
- 중지 버튼으로 현재 변환 중단 가능
- ffmpeg가 없으면 경로 선택 안내 표시
- 손상 파일에서 `moov atom not found` 오류를 설명해줌
- 출력 HEVC 파일에 `hvc1` 태그 적용됨
- 기본 설정에서 FPS가 강제로 30fps로 바뀌지 않음

---

## 15. 핵심 결론

프레임/화질 중심이면 기본 프리셋은 다음으로 잡는 것이 맞다.

```text
CPU x265 10-bit
CRF 20
원본 해상도 유지
FPS 무변경
HDR 메타데이터 유지
HEVC hvc1 출력
AAC 192k 오디오
```
