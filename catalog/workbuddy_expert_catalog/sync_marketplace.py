#!/usr/bin/env python3
"""Synchronize WorkBuddy's official expert marketplace index with local bundles."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def read_manifest(package_root: Path) -> dict:
    for relative in (".codebuddy-plugin/plugin.json", ".workbuddy-plugin/plugin.json", "plugin.json"):
        path = package_root / relative
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugins-root", type=Path, required=True)
    parser.add_argument("--marketplace", type=Path, required=True)
    args = parser.parse_args()

    marketplace = json.loads(args.marketplace.read_text(encoding="utf-8"))
    existing = marketplace.get("plugins") or []
    entries = []
    seen_sources = set()
    for entry in existing:
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source") or "")
        if source and source in seen_sources:
            continue
        if source:
            seen_sources.add(source)
        entries.append(entry)

    added = 0
    updated = 0
    for package_root in sorted(path for path in args.plugins_root.iterdir() if path.is_dir()):
        manifest = read_manifest(package_root)
        if not manifest:
            continue
        source = f"./plugins/{package_root.name}"
        name = str(manifest.get("name") or package_root.name)
        description = manifest.get("description") or ""
        candidate = {"name": name, "source": source, "description": description}
        match = next((entry for entry in entries if entry.get("source") == source), None)
        if match is None:
            entries.append(candidate)
            seen_sources.add(source)
            added += 1
        elif match.get("name") != name or match.get("description") != description:
            match.update(candidate)
            updated += 1

    marketplace["plugins"] = entries
    args.marketplace.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=args.marketplace.parent, delete=False) as handle:
        json.dump(marketplace, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, args.marketplace)
    print(json.dumps({"existing_entries": len(existing), "final_entries": len(entries), "added": added, "updated": updated}, ensure_ascii=False))


if __name__ == "__main__":
    main()
