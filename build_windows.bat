@echo off
setlocal
cd /d "%~dp0"
if not exist "vendor\windows\ffmpeg.exe" (
  echo Place a redistributable ffmpeg.exe at vendor\windows\ffmpeg.exe, then run this script again.
  exit /b 1
)
rmdir /s /q build dist 2>nul
del /q "Video Converter.spec" 2>nul
py -m PyInstaller --noconfirm --windowed --name "Video Converter" --add-binary "vendor\windows\ffmpeg.exe;." video_converter.py
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Video Converter' -DestinationPath 'dist\Video-Converter-windows.zip' -Force"
echo Built: dist\Video-Converter-windows.zip
