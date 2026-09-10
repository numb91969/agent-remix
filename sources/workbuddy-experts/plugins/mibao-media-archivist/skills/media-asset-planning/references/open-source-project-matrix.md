# Built-in reference matrix

These references guide internal implementation; users should not need to install or coordinate the projects themselves.

| Capability | Reference lineage | Mibao internal responsibility |
|---|---|---|
| DV transfer | DVRescue, vrecord | ingest profile, error record, source manifest |
| Technical metadata | MediaInfoLib, ffprobe | normalized metadata schema |
| Video QC | QCTools, MediaConch | quality gates and reports |
| Digital preservation | Archivematica | preservation events and package model |
| Photo/video UX | Immich, PhotoPrism, digiKam | timeline, derivative, and search behavior |
| AI media indexing | Panoptikon | local OCR, ASR, embedding, and hybrid search |
