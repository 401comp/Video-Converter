#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h}"
cd "$ROOT"
CURRENT_INTEL_FFMPEG="$ROOT/vendor/macos/current-intel-x86_64/ffmpeg"
FFMPEG_BIN="${FFMPEG_BIN:-$CURRENT_INTEL_FFMPEG}"
if [[ ! -x "$FFMPEG_BIN" ]]; then
  FFMPEG_BIN="$(command -v ffmpeg || true)"
fi
if [[ -z "$FFMPEG_BIN" || ! -x "$FFMPEG_BIN" ]]; then
  print -u2 "FFmpeg is required. Restore vendor/macos/current-intel-x86_64/ffmpeg, or run FFMPEG_BIN=/path/to/ffmpeg ./build_macos.sh"
  exit 1
fi

ICONSET="assets/Video Converter.iconset"
ICON="assets/Video Converter.icns"
if [[ ! -f "$ICON" ]]; then
  print -u2 "Missing $ICON. Restore the checked-in native app icon before building."
  exit 1
fi

rm -rf build dist "Video Converter.spec"
python3 -m PyInstaller --noconfirm --windowed --name "Video Converter" \
  --icon "$ICON" \
  --add-data "THIRD_PARTY_NOTICES.md:." \
  --add-binary "$FFMPEG_BIN:." video_converter.py
codesign --force --deep --sign - "dist/Video Converter.app"
ditto -c -k --sequesterRsrc --keepParent "dist/Video Converter.app" "dist/Video-Converter-macOS.zip"
codesign --verify --deep --strict "dist/Video Converter.app"
unzip -t "dist/Video-Converter-macOS.zip" >/dev/null
print "Built and verified: $ROOT/dist/Video-Converter-macOS.zip"
