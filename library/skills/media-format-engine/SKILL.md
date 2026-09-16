---
name: media-format-engine
description: Inspect and convert media formats while preserving originals and producing verifiable delivery artifacts.
---

# Media format engine

This is the built-in format processing capability for Mibao. It owns the task from input inspection to verified output.

## Supported task classes

- Video inspection, remux, transcode, proxy generation, audio extraction, and thumbnail/keyframe generation.
- Image inspection, safe derivative generation, resize, and format conversion profiles.
- Audio inspection, extraction, normalization profile planning, and subtitle sidecar export.
- Output verification: existence, size, duration, streams, readability, and checksum.

## Execution contract

Each task accepts an input manifest and configuration, writes only to a new output directory, and produces:

- `processing-log.json`
- `output-manifest.json`
- `failure-list.csv`
- `verification.json`

Never overwrite or delete input files. Never accept arbitrary shell fragments from user input. Commands must be assembled from fixed profiles and validated paths.

## Profiles

- `video-access`: broadly playable access derivative.
- `video-preservation`: preservation-oriented profile, never overwrite the source.
- `image-web`: web/share derivative.
- `image-archive`: archival image derivative.
- `audio-subtitle`: extracted audio and subtitle sidecars.

## Runtime behavior

Use the managed runtime declared in `runtime/manifest.json`. If the required codec runtime is unavailable, return a diagnostic result instead of pretending conversion completed.

## Multimodal verification

When the active model supports image/video/file input, create a visual QA packet after conversion:

- representative first, middle, last, and scene-change frames;
- output technical metadata;
- source-to-output mapping;
- subtitle samples when present;
- verification status.

Ask the multimodal model to inspect the packet for crop, black frames, wrong aspect ratio, unreadable text, subtitle timing/placement, color defects, and obvious audio-video mismatch. The model's visual opinion is a QA signal, not a replacement for deterministic codec, duration, frame, stream, and checksum checks.
