# Third Party Notices

This project bundles FFmpeg and FFprobe binaries in release builds so the desktop app can convert videos without requiring a separate FFmpeg installation.

## FFmpeg

- Project: FFmpeg
- Website: https://ffmpeg.org/
- Source code: https://git.ffmpeg.org/ffmpeg.git
- Legal and license information: https://ffmpeg.org/legal.html
- License: GNU GPL version 3 or later for the bundled builds used by this project

The Windows release bundle downloads the FFmpeg release essentials build from Gyan Doshi's FFmpeg builds:

- https://www.gyan.dev/ffmpeg/builds/

The macOS release bundle downloads FFmpeg and FFprobe release ZIP builds from evermeet.cx:

- https://evermeet.cx/ffmpeg/

The macOS binaries are Intel builds. Apple Silicon Macs may need Rosetta to run the bundled FFmpeg/FFprobe and app bundle.

FFmpeg and FFprobe are distributed as separate executable programs and are invoked by this app through subprocess calls.

Customers may replace the bundled FFmpeg/FFprobe by selecting another executable path inside the app.
