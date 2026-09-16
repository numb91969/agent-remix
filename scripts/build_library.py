#!/usr/bin/env python3
"""Materialize a portable agent-remix library from the merged catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_SUPPORT_FILE_BYTES = 2 * 1024 * 1024
ALLOWED_SUFFIXES = {
    ".cjs",
    ".css",
    ".csv",
    ".html",
    ".ipynb",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
ALLOWED_FILENAMES = {"LICENSE", "LICENCE", "NOTICE", "Makefile"}
SKIP_DIRS = {
    ".git",
    ".cache",
    ".fbs",
    ".review-cache",
    "CSV_Datasets",
    "Databases",
    "Reference_Texts",
    "__pycache__",
    "corpus",
    "dist",
    "node_modules",
    "render-bundle",
    "vendor",
}
SKIP_NAMES = {
    ".env",
    ".env.example",
    ".env.local",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "master.key",
    "secrets.json",
}
SKIP_SUFFIXES = {".cookie", ".key", ".log", ".p12", ".pem", ".pfx", ".session"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the self-contained agent-remix library from merged_catalog.db."
    )
    parser.add_argument(
        "--catalog",
        default="catalog/agency_agents_merged/merged_catalog.db",
        help="Path to the merged SQLite catalog.",
    )
    parser.add_argument(
        "--source-root",
        default=".",
        help="Root containing the relative source paths recorded in the catalog.",
    )
    parser.add_argument(
        "--output",
        default="library",
        help="Destination library directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output directory.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Build with missing source files and record them in index.json.",
    )
    return parser.parse_args()


def row_value(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    return row[key] if key in row.keys() else default


def safe_component(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-._")
    return value or "item"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_source_path(source_root: Path, raw_path: str) -> tuple[Path, str]:
    raw = Path(str(raw_path))
    candidate = raw if raw.is_absolute() else source_root / raw
    resolved_root = source_root.resolve()
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"source path escapes source root: {raw_path}") from exc
    return resolved, relative.as_posix()


def split_paths(value: Any) -> list[str]:
    if not value:
        return []
    return [part for part in str(value).split(";") if part]


def copy_agent(
    row: sqlite3.Row,
    source_root: Path,
    output: Path,
    used_destinations: set[str],
    missing: list[dict[str, str]],
) -> dict[str, Any]:
    raw_source = row_value(row, "local_agent_path") or row_value(row, "source_path")
    source_path = str(raw_source or "")
    entry: dict[str, Any] = {
        "agent_id": row_value(row, "agent_id", ""),
        "source_id": row_value(row, "source_id", ""),
        "source_type": row_value(row, "source_type", ""),
        "source_repo": row_value(row, "source_repo", ""),
        "source_commit": row_value(row, "source_commit", ""),
        "source_path": source_path,
        "language": row_value(row, "language", ""),
        "origin_class": row_value(row, "origin_class", ""),
        "agent_type": row_value(row, "agent_type", ""),
        "plugin": row_value(row, "plugin", ""),
        "name_zh": row_value(row, "name_zh", ""),
        "name_en": row_value(row, "name_en", ""),
        "description_zh": row_value(row, "description_zh", ""),
        "description_en": row_value(row, "description_en", ""),
        "category_raw": row_value(row, "category_raw", ""),
        "domain_id": row_value(row, "domain_id", ""),
        "subcategory": row_value(row, "subcategory", ""),
        "role_stem": row_value(row, "role_stem", ""),
        "family_key": row_value(row, "family_key", ""),
        "family_label_zh": row_value(row, "family_label_zh", ""),
        "family_label_en": row_value(row, "family_label_en", ""),
        "topic_tags": row_value(row, "topic_tags", ""),
        "frontmatter": row_value(row, "frontmatter", ""),
    }

    try:
        source_file, source_rel = resolve_source_path(source_root, source_path)
    except (ValueError, OSError) as exc:
        missing.append(
            {"kind": "agent", "id": str(entry["agent_id"]), "reason": str(exc)}
        )
        entry["bundle_path"] = None
        entry["source_relative_path"] = None
        return entry

    if not source_file.is_file():
        missing.append(
            {
                "kind": "agent",
                "id": str(entry["agent_id"]),
                "reason": f"missing source file: {source_rel}",
            }
        )
        entry["bundle_path"] = None
        entry["source_relative_path"] = source_rel
        return entry

    source_type = safe_component(row_value(row, "source_type", "unknown"))
    base_name = safe_component(str(row_value(row, "agent_id", source_file.stem)))
    destination = Path("agents") / source_type / f"{base_name}.md"
    destination_key = destination.as_posix()
    if destination_key in used_destinations:
        suffix = hashlib.sha256(str(row_value(row, "agent_id", "")).encode()).hexdigest()[:8]
        destination = destination.with_name(f"{destination.stem}-{suffix}.md")
        destination_key = destination.as_posix()
    used_destinations.add(destination_key)

    destination_file = output / destination
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, destination_file)
    entry["source_relative_path"] = source_rel
    entry["bundle_path"] = destination.as_posix()
    entry["sha256"] = sha256_file(destination_file)
    return entry


def should_skip_file(path: Path, relative: Path) -> str | None:
    if path.is_symlink():
        return "symlink"
    if any(part in SKIP_DIRS for part in relative.parts):
        return "excluded directory"
    if path.name in SKIP_NAMES:
        return "credential-like filename"
    if path.suffix.lower() in SKIP_SUFFIXES:
        return "credential-like suffix"
    if path.name.startswith(".env"):
        return "environment file"
    if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name not in ALLOWED_FILENAMES:
        return "non-portable binary or unknown file type"
    try:
        if path.stat().st_size > MAX_SUPPORT_FILE_BYTES and path.name != "SKILL.md":
            return f"larger than {MAX_SUPPORT_FILE_BYTES} bytes"
    except OSError as exc:
        return f"stat failed: {exc}"
    return None


def materialize_skill(
    slug: str,
    source_paths: list[str],
    source_root: Path,
    output: Path,
    catalog_record: dict[str, Any],
    missing: list[dict[str, str]],
) -> dict[str, Any]:
    destination = Path("skills") / safe_component(slug)
    destination_dir = output / destination
    destination_dir.mkdir(parents=True, exist_ok=True)
    selected_source: Path | None = None
    selected_source_rel: str | None = None

    for raw_path in source_paths:
        try:
            candidate, candidate_rel = resolve_source_path(source_root, raw_path)
        except (ValueError, OSError):
            continue
        if candidate.is_dir():
            selected_source = candidate
            selected_source_rel = candidate_rel
            break

    entry = dict(catalog_record)
    entry["skill_slug"] = slug
    entry["source_paths"] = source_paths
    entry["bundle_path"] = destination.as_posix()
    entry["bundle_files"] = []
    entry["excluded_files"] = []
    entry["selected_source_path"] = selected_source_rel

    if selected_source is None:
        missing.append(
            {
                "kind": "skill",
                "id": slug,
                "reason": "none of the recorded source directories exists",
            }
        )
        entry["status"] = "missing"
        return entry

    for path in sorted(selected_source.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(selected_source)
        reason = should_skip_file(path, relative)
        if reason:
            entry["excluded_files"].append({"path": relative.as_posix(), "reason": reason})
            continue
        target = destination_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        entry["bundle_files"].append(relative.as_posix())

    skill_md = destination_dir / "SKILL.md"
    if not skill_md.is_file():
        missing.append(
            {
                "kind": "skill",
                "id": slug,
                "reason": f"selected source has no SKILL.md: {selected_source_rel}",
            }
        )
        entry["status"] = "missing-skill-md"
    else:
        entry["status"] = "bundled"
        entry["skill_md_sha256"] = sha256_file(skill_md)
    return entry


def discover_unbound_skills(source_root: Path, known: dict[str, dict[str, Any]]) -> None:
    plugin_root = source_root / "sources" / "workbuddy-experts" / "plugins"
    if not plugin_root.is_dir():
        return
    extra_paths: dict[str, list[str]] = defaultdict(list)
    for skill_md in sorted(plugin_root.rglob("SKILL.md")):
        try:
            relative = skill_md.parent.relative_to(source_root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        slug = skill_md.parent.name
        if slug not in known:
            extra_paths[slug].append(relative.as_posix())
    for slug, paths in extra_paths.items():
        known[slug] = {
            "skill_slug": slug,
            "expert_count": 0,
            "downloaded_count": 1,
            "source_ids": "",
            "cataloged": False,
            "unbound_source": True,
            "_source_paths": paths,
        }


def write_library_readme(output: Path, index: dict[str, Any]) -> None:
    counts = index["counts"]
    text = f"""# Bundled Agent Library

This directory is materialized by scripts/build_library.py and is shipped inside the
agent-remix skill. It is intentionally self-contained: normal search and extraction do
not fetch another repository.

- Agents: {counts["agents"]}
- Cataloged skills: {counts["catalog_skills"]}
- Bundled skills, including locally discovered unbound skills: {counts["skills"]}
- Agent-skill bindings: {counts["bindings"]}
- Missing or excluded source records: {counts["missing_records"]}

Use index.json with scripts/agent_remix.py. Each agent and skill keeps its original
source repository, commit, relative source path, and content hash when that metadata was
available.
"""
    (output / "README.md").write_text(text, encoding="utf-8")


def write_sources_notice(output: Path, index: dict[str, Any]) -> None:
    lines = [
        "# Bundled Source Notice",
        "",
        "The library is a materialized collection of prompts and skill documents from the",
        "source snapshots recorded in index.json. Review each upstream license before",
        "redistributing or publishing a generated agent.",
        "",
        "## Source repositories",
        "",
    ]
    sources: dict[tuple[str, str], str] = {}
    for agent in index["agents"]:
        key = (str(agent.get("source_repo") or ""), str(agent.get("source_commit") or ""))
        if key != ("", ""):
            sources[key] = "agent prompts"
    for (repo, commit), label in sorted(sources.items()):
        lines.append(f"- {repo} at {commit} ({label})")
    lines.extend(
        [
            "",
            "The package excludes credentials, absolute links, caches, large datasets,",
            "and selected non-portable binaries. See each skill entry's excluded_files",
            "field for the materialized support-file boundary.",
        ]
    )
    (output / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> int:
    catalog = Path(args.catalog).resolve()
    source_root = Path(args.source_root).resolve()
    output = Path(args.output).resolve()
    if not catalog.is_file():
        print(f"catalog not found: {catalog}", file=sys.stderr)
        return 2
    if not source_root.is_dir():
        print(f"source root not found: {source_root}", file=sys.stderr)
        return 2
    if output.exists():
        if not args.force:
            print(f"output exists; pass --force to replace: {output}", file=sys.stderr)
            return 2
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(catalog)
    connection.row_factory = sqlite3.Row
    try:
        agent_rows = connection.execute("SELECT * FROM agents ORDER BY agent_id").fetchall()
        skill_rows = connection.execute("SELECT * FROM skills ORDER BY skill_slug").fetchall()
        binding_rows = connection.execute(
            "SELECT agent_id, skill_slug, local_skill_path, link_path, skill_status "
            "FROM agent_skills ORDER BY agent_id, skill_slug"
        ).fetchall()
    finally:
        connection.close()

    bindings_by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bindings: list[dict[str, Any]] = []
    for row in binding_rows:
        binding = {
            "agent_id": row_value(row, "agent_id", ""),
            "skill_slug": row_value(row, "skill_slug", ""),
            "local_skill_path": row_value(row, "local_skill_path", ""),
            "link_path": row_value(row, "link_path", ""),
            "skill_status": row_value(row, "skill_status", ""),
        }
        bindings.append(binding)
        bindings_by_agent[str(binding["agent_id"])].append(binding)

    missing: list[dict[str, str]] = []
    used_agent_destinations: set[str] = set()
    agents: list[dict[str, Any]] = []
    for row in agent_rows:
        entry = copy_agent(
            row, source_root, output, used_agent_destinations, missing
        )
        entry["skills"] = bindings_by_agent.get(str(entry["agent_id"]), [])
        agents.append(entry)

    skills_by_slug: dict[str, dict[str, Any]] = {}
    for row in skill_rows:
        slug = str(row_value(row, "skill_slug", ""))
        skills_by_slug[slug] = {
            "skill_slug": slug,
            "expert_count": row_value(row, "expert_count", 0),
            "downloaded_count": row_value(row, "downloaded_count", 0),
            "source_ids": row_value(row, "source_ids", ""),
            "cataloged": True,
            "_source_paths": split_paths(row_value(row, "local_paths", "")),
        }
    catalog_skill_count = len(skills_by_slug)
    discover_unbound_skills(source_root, skills_by_slug)

    skills: list[dict[str, Any]] = []
    for slug in sorted(skills_by_slug):
        record = skills_by_slug[slug]
        skills.append(
            materialize_skill(
                slug,
                record.pop("_source_paths", []),
                source_root,
                output,
                record,
                missing,
            )
        )

    known_skill_slugs = {str(skill["skill_slug"]) for skill in skills}
    for binding in bindings:
        if str(binding["skill_slug"]) not in known_skill_slugs:
            missing.append(
                {
                    "kind": "binding",
                    "id": f'{binding["agent_id"]}:{binding["skill_slug"]}',
                    "reason": "binding has no bundled skill record",
                }
            )

    index: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "package": "agent-remix",
        "self_contained": True,
        "counts": {
            "agents": len(agents),
            "catalog_skills": catalog_skill_count,
            "skills": len(skills),
            "bindings": len(bindings),
            "missing_records": len(missing),
        },
        "build_policy": {
            "max_support_file_bytes": MAX_SUPPORT_FILE_BYTES,
            "allowed_support_suffixes": sorted(ALLOWED_SUFFIXES),
            "excluded_directories": sorted(SKIP_DIRS),
            "network_used": False,
        },
        "agents": agents,
        "skills": skills,
        "bindings": bindings,
        "missing": missing,
    }
    (output / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_library_readme(output, index)
    write_sources_notice(output, index)

    print(
        json.dumps(
            {
                "output": str(output),
                "agents": len(agents),
                "catalog_skills": catalog_skill_count,
                "bundled_skills": len(skills),
                "bindings": len(bindings),
                "missing_records": len(missing),
            },
            ensure_ascii=False,
        )
    )
    if missing and not args.allow_missing:
        print(
            "library build incomplete; rerun with --allow-missing only if the omissions are intentional",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(build(parse_args()))
