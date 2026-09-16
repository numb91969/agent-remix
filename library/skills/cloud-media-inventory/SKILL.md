---
name: cloud-media-inventory
description: Enumerate cloud media sources with resumable pagination, source snapshots, unified asset manifests, duplicate candidates, and auditable delivery.
---

# Cloud media inventory

Use this skill when the user asks to inspect, compare, inventory, or plan processing for Weiyun, WeCom Disk, or another connected cloud media source.

## Workflow

1. Confirm provider scope and read-only policy.
2. Run connector capability/auth check before listing.
3. Enumerate page by page; persist the raw response before advancing.
4. Record provider, space/library, cursor or server version, page number, response hash, count, has-more/finish flag, and errors.
5. Normalize each remote item into the unified asset record without discarding provider fields.
6. Build observed counts and totals. Only expose total counts when the source is complete.
7. Generate duplicate candidates from name/size/metadata, and reserve `confirmed_duplicate` for downloaded SHA-256 matches.
8. Build a priority queue with evidence, expected outputs, processing cost, and user confirmation needs.
9. Render report and acceptance receipt; preserve partial and blocked states.

## Required artifacts

- source-snapshot.json
- page-manifest.jsonl and raw page files
- asset-manifest.jsonl
- duplicate-candidates.json
- priority-queue.json
- scan-log.jsonl
- acceptance.json
- report.html or report.md

## States

Use `complete`, `partial`, `blocked`, `retryable`, `changed`, `inaccessible`, and `unknown`. A partial scan must use `observedCount`, never pretend it is the source total.

## Safety

Cloud sources are read-only by default. Never delete, move, rename, publish, or upload originals without explicit confirmation. Download only to a separate derived workspace after scope, destination, disk space, and privacy are confirmed.
