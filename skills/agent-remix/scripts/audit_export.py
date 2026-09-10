#!/usr/bin/env python3
"""Audit an agent-remix export for secrets, broken links, and oversized files."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


SECRET_NAME = re.compile(
    r"(?i)(^|/)(\.env(?:\..*)?|id_(?:rsa|ed25519)|[^/]+\.(?:pem|p12|pfx|key)|(?:credentials?|secrets?)\.(?:json|ya?ml|toml)|[^/]*(?:master|secret)[_-](?:key|token)\.(?:json|ya?ml|toml|env))$"
)
SECRET_TEXT = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret|private[_-]?key)\b\s*[:=]\s*[\"']([A-Za-z0-9+/=_\-.]{16,})[\"']"
)
BEARER_TEXT = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{24,}")
PLACEHOLDER_VALUE = re.compile(r"(?i)^(?:your[_-]|<|redacted|example|placeholder|dummy|test[_-])")
ABSOLUTE_USER_PATH = re.compile(r"/Users/[^\s'\"`]+|/home/[^\s'\"`]+")
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".csv", ".tsv",
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".sh", ".sql", ".html", ".css",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-mb", type=float, default=10.0)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR missing export directory: {root}")
        return 2

    high = 0
    warnings = 0
    files = 0
    total = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == "skills/agent-remix/scripts/audit_export.py":
            continue
        if path.is_symlink():
            target = path.resolve(strict=False)
            if not target.exists():
                print(f"HIGH broken symlink: {rel} -> {path.readlink()}")
                high += 1
            elif target.is_absolute() and root not in target.parents:
                print(f"WARN external symlink: {rel} -> {path.readlink()}")
                warnings += 1
            continue
        if not path.is_file():
            continue
        files += 1
        size = path.stat().st_size
        total += size
        if SECRET_NAME.search(rel):
            print(f"HIGH sensitive filename: {rel}")
            high += 1
        if size > args.max_mb * 1024 * 1024:
            print(f"WARN oversized file ({size / 1024 / 1024:.1f} MiB): {rel}")
            warnings += 1
        if path.suffix.lower() in TEXT_EXTENSIONS and size <= 4 * 1024 * 1024:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"WARN unreadable text {rel}: {exc}")
                warnings += 1
                continue
            assignment_is_secret = any(
                not PLACEHOLDER_VALUE.search(match.group(2))
                for match in SECRET_TEXT.finditer(content)
            )
            if assignment_is_secret or BEARER_TEXT.search(content):
                print(f"HIGH credential-like assignment: {rel}")
                high += 1
            if ABSOLUTE_USER_PATH.search(content):
                print(f"WARN absolute user path: {rel}")
                warnings += 1

    print(f"SUMMARY files={files} bytes={total} high={high} warnings={warnings}")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
