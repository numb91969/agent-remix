# Index contract

The index is a derived, rebuildable representation of the media library.

## Required fields

- stable asset ID
- absolute path and relative path
- source size, modification time, media type, MIME type
- SHA-256 when enabled
- technical metadata JSON
- processing status
- AI-derived result references

## Safety

Scanning is read-only. Index databases and derived files must live outside the source tree unless the user explicitly selects an output directory. A missing source file is reported, not deleted from the database silently.
