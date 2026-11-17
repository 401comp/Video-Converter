# Third-party notices

## FFmpeg current static build for macOS x86_64

This app bundles the `ffmpeg` executable from the current Intel macOS static build published by Evermeet, which is linked from FFmpeg's official download page:

`https://evermeet.cx/ffmpeg/`

Bundled snapshot: `N-128812-ga337e8ddaa0-tessus` (compiled 2026-11-11). The SHA-256 of the bundled executable is:

`0e146cdf6feb6764e54c211d48ee29ab8d33d6ad9df31004218bdbf6686c2751`

FFmpeg is licensed under LGPL 2.1+ or GPL 2+, depending on enabled components. This build enables GPL components. FFmpeg source and license information are available at `https://ffmpeg.org/legal.html` and `https://ffmpeg.org/download.html`.

The build identifies itself as `N-128812-ga337e8ddaa0-tessus`; its exact
configuration is available from `ffmpeg -buildconf` in the bundled executable.
The Video Converter source repository contains the application build scripts;
the upstream FFmpeg source for this snapshot is available from the FFmpeg Git
repository at commit `a337e8ddaa0`.
