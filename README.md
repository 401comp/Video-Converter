# Video Converter

A simple local desktop app for converting videos without uploading them anywhere.

It accepts common video files including **WEBM, MP4, MOV, MKV, AVI, M4V, MPEG, WMV, and FLV**. Output choices are **MP4, MOV, MKV, WEBM, and AVI**. Add a batch of files, choose a format and quality setting, and convert. Originals are never changed; each result gets a `_converted` filename.

The built macOS app includes a native-resolution Dock icon generated from the project’s editable `assets/video-converter-icon.svg`.

## macOS release build

Requirements: Python 3, PyInstaller, and an executable FFmpeg build with `libx264`, `aac`, `libvpx-vp9`, and `libopus` enabled.

```zsh
python3 -m pip install pyinstaller
./build_macos.sh
```

The build script embeds the supplied self-contained current Intel FFmpeg binary from `vendor/macos/current-intel-x86_64/ffmpeg`. It produces a current Intel macOS release, tested on macOS Sequoia. The script ad-hoc signs the app and checks both the app signature and ZIP archive. Deliverable:

`dist/Video-Converter-macOS.zip`

Unzip it and drag **Video Converter.app** into Applications.

The supplied macOS build is an Intel release for current Intel Macs. Apple Silicon is not a supported target for this package; build separately with an ARM64 or universal Python runtime and FFmpeg bundle when that becomes a release target. The source and Windows build recipe are cross-platform, but Windows binaries must be built on Windows.

## Windows release build

Put a trusted, redistributable `ffmpeg.exe` in `vendor/windows/ffmpeg.exe`, then run `build_windows.bat` on Windows. It creates `dist/Video-Converter-windows.zip` containing the app and its bundled FFmpeg.

## Codec notes

MP4/MOV/MKV/AVI outputs use MPEG-4 video and AAC audio for broad playback compatibility. WEBM outputs use VP9 and Opus. Some source files or FFmpeg builds may not support a requested codec; the app shows FFmpeg's error instead of silently creating junk.

## License

Video Converter is distributed under the GNU General Public License, version
3. The included FFmpeg build enables GPL components; the corresponding source
and build configuration are documented in `THIRD_PARTY_NOTICES.md`.

## Support

Found a problem? [Report it on GitHub](https://github.com/401comp/Video-Converter/issues/new?template=bug_report.md).
Please include the app version, your macOS version, and the input/output formats,
but never upload private video files.
