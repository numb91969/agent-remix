# Supported format policy

The format engine distinguishes source, preservation derivative, access derivative, and AI working derivative.

## Initial access targets

- Video: MP4 with H.264/AAC for broad playback.
- Audio: WAV for working and preservation workflows; AAC/MP3 only for access copies.
- Images: JPEG for access copies; TIFF for archive derivatives when the runtime supports it.
- Subtitles: SRT and WebVTT.

## Rules

- Keep the source file unchanged.
- Record the source hash and output hash.
- Record the exact profile and runtime version.
- Do not call a derivative a preservation master unless its profile and verification policy have passed.
