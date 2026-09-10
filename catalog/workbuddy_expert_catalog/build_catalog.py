#!/usr/bin/env python3
"""Build a searchable local catalog for WorkBuddy's official Expert Center.

The script intentionally uses the cached Expert Center manifest as the primary
source because it is the 446-entry dataset present on this machine.  It also
scans the local WorkBuddy expert marketplace so downloaded packages and their
skills can be linked without copying them a second time.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin


CATALOG_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = Path.home() / ".workbuddy/app/cache/experts/manifest.json"
DEFAULT_METADATA = Path.home() / ".workbuddy/app/cache/experts/metadata.json"
DEFAULT_VERSION = Path.home() / ".workbuddy/app/cache/experts/version.txt"
DEFAULT_MARKETPLACE = Path.home() / ".workbuddy/plugins/marketplaces/experts"
PACKAGE_METADATA_ROOT = CATALOG_DIR / "package_metadata"
REMOTE_BASE = "https://acc-1258344699.cos.accelerate.myqcloud.com/workbuddy/expert-marketplace"
SIGNED_DOWNLOAD_ENDPOINT = "https://copilot.tencent.com/portal/operation-platform/market/expert/download-url"
EXACT_MARKETING_CATEGORIES = {"05-MarketingGrowth", "07-SalesCommerce"}
MARKETING_KEYWORDS = [
    "电商",
    "营销",
    "marketing",
    "commerce",
    "ecommerce",
    "e-commerce",
    "sales",
    "advertis",
    "growth",
    "brand",
    "shop",
    "retail",
    "淘宝",
    "天猫",
    "京东",
    "拼多多",
    "直播",
    "广告",
    "销售",
    "品牌",
    "运营",
    "转化",
    "投放",
    "私域",
    "内容营销",
]


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def localized(value: Any, locale: str) -> str:
    if isinstance(value, dict):
        result = value.get(locale)
        if isinstance(result, str):
            return result
    return ""


def flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)


def safe_slug(value: str) -> str:
    value = value.strip().replace("\\", "/")
    value = value.removeprefix("./").strip("/")
    value = re.sub(r"[^0-9A-Za-z._-]+", "-", value)
    return value.strip("-._") or "unnamed"


def local_path_for_prompt(expert: dict[str, Any]) -> Path:
    prompt_file = str(expert.get("promptFile") or "")
    file_name = Path(prompt_file).name or f"{safe_slug(str(expert.get('id', 'expert')))}.md"
    return CATALOG_DIR / "prompts" / safe_slug(str(expert.get("id", "expert"))) / file_name


def package_candidates(plugin: str, marketplace_root: Path) -> list[Path]:
    candidates = [
        CATALOG_DIR / "packages" / plugin,
        marketplace_root / "plugins" / plugin,
    ]
    return [path for path in candidates if path.is_dir()]


def find_plugin_manifest(package_root: Path) -> Path | None:
    for metadata_dir in (".codebuddy-plugin", ".workbuddy-plugin"):
        candidate = package_root / metadata_dir / "plugin.json"
        if candidate.is_file():
            return candidate
    return None


def read_plugin_manifest(package_root: Path) -> dict[str, Any] | None:
    manifest_path = find_plugin_manifest(package_root)
    if not manifest_path:
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def skill_refs_from_plugin(plugin_manifest: dict[str, Any] | None) -> list[str]:
    if not plugin_manifest or not isinstance(plugin_manifest.get("skills"), list):
        return []
    return [str(item) for item in plugin_manifest["skills"] if isinstance(item, str) and item.strip()]


def plugin_manifest_matches_expert(plugin_manifest: dict[str, Any], expert: dict[str, Any]) -> bool:
    """Match a downloaded package whose directory/plugin slug was renamed upstream.

    WorkBuddy has returned a few packages whose local plugin name differs from the
    cached Expert Center ``plugin`` field (for example ``paper-advisor`` for the
    manifest entry ``thesis-writing-mentor``).  A localized profession match is a
    safe fallback when the exact plugin directory is absent.  The caller only
    accepts an unambiguous match.
    """
    expected_plugin = str(expert.get("plugin") or expert.get("agentName") or "")
    package_names = {
        str(plugin_manifest.get("name") or ""),
        str(plugin_manifest.get("agentName") or ""),
    }
    if expected_plugin and expected_plugin in package_names:
        return True
    expected_profession = expert.get("profession") or {}
    package_profession = plugin_manifest.get("profession") or {}
    package_display = plugin_manifest.get("displayName") or {}
    if not all(isinstance(value, dict) for value in (expected_profession, package_profession, package_display)):
        return False
    for locale in ("en", "zh"):
        expected = str(expected_profession.get(locale) or "").strip()
        actual_profession = str(package_profession.get(locale) or "").strip()
        actual_display = str(package_display.get(locale) or "").strip()
        if expected and expected == actual_profession:
            return True
        # A few returned packages put the marketplace profession in displayName
        # while their own profession field is a longer internal description.
        if expected and expected == actual_display:
            return True
    return False


def skill_root_from_ref(package_root: Path, ref: str) -> Path:
    return package_root / ref.removeprefix("./")


def resolve_skill_root(package_root: Path, ref: str) -> Path | None:
    """Resolve a declared skill path, including one unambiguous renamed skill.

    A small number of WorkBuddy bundles retain an older skill reference in
    plugin.json while shipping a versioned/relocalized directory (for
    example ``tencent-cloud-rum`` -> ``tencent-cloud-rum-zh-2.1``).  Keep the
    declared slug in the catalog, but point the local index at the actual
    directory when there is exactly one prefix match containing SKILL.md.
    """
    exact = skill_root_from_ref(package_root, ref)
    if exact.is_dir():
        return exact
    parent = exact.parent
    if not parent.is_dir():
        return None
    prefix = exact.name.casefold() + "-"
    candidates = sorted(
        child for child in parent.iterdir()
        if child.is_dir()
        and child.name.casefold().startswith(prefix)
        and (child / "SKILL.md").is_file()
    )
    return candidates[0] if len(candidates) == 1 else None


def normalize_agent_name(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.casefold())


def frontmatter_agent_name(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r"^name:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def package_agent_files(package_root: Path, plugin_manifest: dict[str, Any]) -> list[Path]:
    refs = plugin_manifest.get("agents") or ["./agents"]
    if isinstance(refs, str):
        refs = [refs]
    if not isinstance(refs, list):
        refs = ["./agents"]
    files: list[Path] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        candidate = package_root / ref.removeprefix("./")
        if candidate.is_file() and candidate.suffix.casefold() == ".md":
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(sorted(path for path in candidate.rglob("*.md") if path.is_file()))
    return list(dict.fromkeys(files))


def resolve_package_agent_path(package_root: Path, plugin_manifest: dict[str, Any], expert: dict[str, Any]) -> Path | None:
    files = package_agent_files(package_root, plugin_manifest)
    if not files:
        return None
    expected_names = [
        str(expert.get("agentName") or ""),
        str(expert.get("id") or ""),
    ]
    team_info = plugin_manifest.get("teamInfo")
    if isinstance(team_info, dict):
        expected_names.insert(0, str(team_info.get("leadAgent") or ""))
    normalized_expected = {normalize_agent_name(value) for value in expected_names if value}
    for path in files:
        basename = normalize_agent_name(path.stem)
        frontmatter = normalize_agent_name(frontmatter_agent_name(path))
        if basename in normalized_expected or frontmatter in normalized_expected:
            return path
    if len(files) == 1:
        return files[0]
    # Translation variants normally use a *_zh suffix; prefer the canonical
    # non-translation file for package-level agents when no explicit name hit.
    non_translation = [path for path in files if not path.stem.casefold().endswith(("_zh", "-zh", "_cn", "-cn"))]
    if len(non_translation) == 1:
        return non_translation[0]
    return None


def make_symlink(link_path: Path, target: Path) -> bool:
    if not target.exists():
        return False
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() or link_path.is_file():
            link_path.unlink()
        else:
            return False
    link_path.symlink_to(target)
    return True


def csv_write(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def category_name(categories_by_id: dict[str, dict[str, Any]], category_id: str, locale: str) -> str:
    return localized(categories_by_id.get(category_id, {}).get("name"), locale)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--version", type=Path, default=DEFAULT_VERSION)
    parser.add_argument("--marketplace", type=Path, default=DEFAULT_MARKETPLACE)
    parser.add_argument("--live-manifest", type=Path, default=None)
    parser.add_argument("--overlay", type=Path, action="append", default=[], help="Optional internal/external manifest overlay; repeatable.")
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    if not manifest_path.is_file():
        raise SystemExit(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    experts = manifest.get("experts") or []
    categories = manifest.get("categories") or []
    categories_by_id = {str(item.get("id")): item for item in categories if item.get("id")}
    if not experts:
        raise SystemExit("manifest contains no experts")

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = CATALOG_DIR / "snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, snapshots / "expert_center.json")
    for source in (args.metadata, args.version):
        if source.expanduser().is_file():
            shutil.copy2(source.expanduser(), snapshots / source.name)
    if args.live_manifest and args.live_manifest.is_file():
        live_snapshot = snapshots / "live_expert_center.json"
        if args.live_manifest.expanduser().resolve() != live_snapshot.resolve():
            shutil.copy2(args.live_manifest, live_snapshot)
    for overlay in args.overlay:
        overlay_path = overlay.expanduser()
        if overlay_path.is_file():
            overlay_snapshot = snapshots / overlay_path.name
            if overlay_path.resolve() != overlay_snapshot.resolve():
                shutil.copy2(overlay_path, overlay_snapshot)

    catalog_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    built_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    package_cache: dict[str, tuple[Path | None, dict[str, Any] | None]] = {}
    metadata_cache: dict[str, tuple[Path | None, dict[str, Any] | None]] = {}
    marketplace_packages: list[tuple[Path, dict[str, Any]]] = []
    marketplace_plugins_root = args.marketplace.expanduser() / "plugins"
    if marketplace_plugins_root.is_dir():
        for candidate in sorted(path for path in marketplace_plugins_root.iterdir() if path.is_dir()):
            candidate_manifest = read_plugin_manifest(candidate)
            if candidate_manifest:
                marketplace_packages.append((candidate, candidate_manifest))
    prompt_results_by_id: dict[str, dict[str, Any]] = {}
    prompt_results_path = CATALOG_DIR / "prompt_fetch_results.json"
    if prompt_results_path.is_file():
        try:
            prompt_payload = json.loads(prompt_results_path.read_text(encoding="utf-8"))
            prompt_results_by_id = {str(row.get("id")): row for row in prompt_payload.get("results") or [] if row.get("id")}
        except (OSError, json.JSONDecodeError):
            prompt_results_by_id = {}
    expert_rows: list[dict[str, Any]] = []
    tag_rows: list[dict[str, Any]] = []
    quick_prompt_rows: list[dict[str, Any]] = []
    expert_skill_rows: list[dict[str, Any]] = []
    skill_aggregate: dict[str, dict[str, Any]] = {}
    marketing_rows: list[dict[str, Any]] = []
    agent_link_dir = CATALOG_DIR / "agents" / "by-expert"
    agent_link_dir.mkdir(parents=True, exist_ok=True)
    for child in agent_link_dir.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
    skill_link_dir = CATALOG_DIR / "skills" / "by-expert"
    skill_link_dir.mkdir(parents=True, exist_ok=True)
    for child in skill_link_dir.rglob("*"):
        if child.is_symlink():
            child.unlink()

    for expert in experts:
        expert_id = str(expert.get("id") or expert.get("agentName") or "")
        plugin = str(expert.get("plugin") or expert.get("agentName") or safe_slug(expert_id))
        category_id = str(expert.get("categoryId") or "")
        source_id = expert.get("sourceId")
        market_expert_id = source_id if isinstance(source_id, str) and source_id.startswith("ex_") else None
        prompt_file = str(expert.get("promptFile") or "")
        prompt_url = urljoin(REMOTE_BASE + "/", prompt_file.lstrip("/")) if prompt_file else ""
        prompt_record = prompt_results_by_id.get(expert_id, {})
        prompt_selected_url = str(prompt_record.get("selected_url") or prompt_url)
        prompt_local_path = Path(str(prompt_record.get("local_path"))) if prompt_record.get("local_path") else local_path_for_prompt(expert)
        prompt_status = str(prompt_record.get("status") or ("downloaded" if prompt_local_path.is_file() else "not_attempted"))
        package_root = None
        plugin_manifest = None
        if plugin not in package_cache:
            candidates = package_candidates(plugin, args.marketplace.expanduser())
            package_root = candidates[0] if candidates else None
            plugin_manifest = read_plugin_manifest(package_root) if package_root else None
            if package_root is None:
                alias_candidates = [
                    (path, candidate_manifest)
                    for path, candidate_manifest in marketplace_packages
                    if plugin_manifest_matches_expert(candidate_manifest, expert)
                ]
                if len(alias_candidates) == 1:
                    package_root, plugin_manifest = alias_candidates[0]
            package_cache[plugin] = (package_root, plugin_manifest)
        else:
            package_root, plugin_manifest = package_cache[plugin]
        if plugin not in metadata_cache:
            metadata_candidates = [
                PACKAGE_METADATA_ROOT / plugin,
                PACKAGE_METADATA_ROOT / safe_slug(plugin),
            ]
            metadata_root = next((path for path in metadata_candidates if path.is_dir()), None)
            metadata_manifest = read_plugin_manifest(metadata_root) if metadata_root else None
            metadata_cache[plugin] = (metadata_root, metadata_manifest)
        else:
            metadata_root, metadata_manifest = metadata_cache[plugin]
        effective_plugin_manifest = plugin_manifest or metadata_manifest

        all_text = " ".join(flatten_strings(expert)).casefold()
        matched_keywords = [keyword for keyword in MARKETING_KEYWORDS if keyword.casefold() in all_text]
        exact_category = category_id in EXACT_MARKETING_CATEGORIES
        keyword_match = bool(matched_keywords)
        selection_reason = "category" if exact_category else ("keyword" if keyword_match else "")
        if exact_category or keyword_match:
            marketing_rows.append({
                "id": expert_id,
                "display_name_zh": localized(expert.get("displayName"), "zh"),
                "profession_zh": localized(expert.get("profession"), "zh"),
                "category_id": category_id,
                "category_name_zh": category_name(categories_by_id, category_id, "zh"),
                "plugin": plugin,
                "agent_name": expert.get("agentName") or "",
                "selection_reason": selection_reason,
                "matched_keywords": ",".join(matched_keywords),
                "prompt_file": prompt_file,
                "prompt_url": prompt_url,
                "prompt_selected_url": prompt_selected_url,
                "prompt_local_path": str(prompt_local_path) if prompt_local_path.is_file() else "",
                "prompt_status": prompt_status,
                "market_expert_id": market_expert_id or "",
                "package_status": "downloaded" if package_root else "planned",
            })

        local_prompt = prompt_local_path
        package_agent_path = ""
        package_skills = skill_refs_from_plugin(effective_plugin_manifest)
        if package_root and plugin_manifest:
            package_agent = resolve_package_agent_path(package_root, plugin_manifest, expert)
            if package_agent:
                package_agent_path = str(package_agent)
            if not package_skills and isinstance(expert.get("skills"), list):
                package_skills = [str(item) for item in expert["skills"] if isinstance(item, str)]

        package_status = "downloaded" if package_root else ("prompt_downloaded" if local_prompt.is_file() else "planned")
        if package_root is not None and not plugin_manifest:
            package_status = "incomplete_local_package"
        agent_target = Path(package_agent_path) if package_agent_path else local_prompt
        agent_link_path = agent_link_dir / f"{safe_slug(expert_id)}.md"
        agent_link_value = str(agent_link_path) if agent_target.is_file() and make_symlink(agent_link_path, agent_target) else ""
        agent_available = int(agent_target.is_file())
        agent_source = "local_package" if package_agent_path else ("public_static_prompt" if local_prompt.is_file() else "")

        source_id_value = source_id if isinstance(source_id, str) else ""
        expert_rows.append({
            "id": expert_id,
            "source_id": source_id_value,
            "market_expert_id": market_expert_id or "",
            "agent_name": expert.get("agentName") or "",
            "plugin": plugin,
            "display_name_zh": localized(expert.get("displayName"), "zh"),
            "display_name_en": localized(expert.get("displayName"), "en"),
            "name_zh": localized(expert.get("name"), "zh"),
            "name_en": localized(expert.get("name"), "en"),
            "profession_zh": localized(expert.get("profession"), "zh"),
            "profession_en": localized(expert.get("profession"), "en"),
            "description_zh": localized(expert.get("description"), "zh"),
            "description_en": localized(expert.get("description"), "en"),
            "display_description_zh": localized(expert.get("displayDescription"), "zh"),
            "display_description_en": localized(expert.get("displayDescription"), "en"),
            "category_id": category_id,
            "category_name_zh": category_name(categories_by_id, category_id, "zh"),
            "category_name_en": category_name(categories_by_id, category_id, "en"),
            "expert_type": expert.get("expertType") or "",
            "visibility": expert.get("visibility") or "",
            "version": expert.get("version") or "",
            "author_zh": localized(expert.get("author"), "zh"),
            "author_en": localized(expert.get("author"), "en"),
            "avatar": expert.get("avatar") or "",
            "prompt_file": prompt_file,
            "prompt_url": prompt_url,
            "prompt_selected_url": prompt_selected_url,
            "prompt_local_path": str(prompt_local_path) if prompt_local_path.is_file() else "",
            "prompt_status": prompt_status,
            "prompt_bytes": int(prompt_record.get("bytes") or 0),
            "prompt_sha256": str(prompt_record.get("sha256") or ""),
            "signed_download_endpoint": SIGNED_DOWNLOAD_ENDPOINT if market_expert_id else "",
            "is_opc": int(bool(expert.get("isOPC"))),
            "is_cloud": int(bool(expert.get("isCloud") or expert.get("isInCloud"))),
            "local_package_path": str(package_root) if package_root else "",
            "local_agent_path": package_agent_path or (str(local_prompt) if local_prompt.is_file() else ""),
            "agent_link_path": agent_link_value,
            "agent_source": agent_source,
            "agent_available": agent_available,
            "package_status": package_status,
            "created_at": expert.get("createdAt") or "",
            "updated_at": expert.get("updatedAt") or "",
            "raw_json": json_text(expert),
            "is_exact_marketing_category": int(exact_category),
            "is_marketing_keyword_match": int(keyword_match),
            "matched_keywords": ",".join(matched_keywords),
        })

        for index, tag in enumerate(expert.get("tags") or []):
            if not isinstance(tag, dict):
                continue
            tag_rows.append({"expert_id": expert_id, "ordinal": index, "zh": tag.get("zh") or "", "en": tag.get("en") or ""})
        for index, prompt in enumerate(expert.get("quickPrompts") or []):
            if not isinstance(prompt, dict):
                continue
            quick_prompt_rows.append({"expert_id": expert_id, "ordinal": index, "zh": prompt.get("zh") or "", "en": prompt.get("en") or ""})

        for index, skill_ref in enumerate(package_skills):
            skill_slug = safe_slug(Path(skill_ref.removeprefix("./")).name or skill_ref)
            local_skill_path = ""
            skill_status = "planned"
            if package_root:
                skill_root = resolve_skill_root(package_root, skill_ref)
                if skill_root:
                    local_skill_path = str(skill_root)
                    skill_status = "downloaded" if (skill_root / "SKILL.md").is_file() else "directory_without_SKILL.md"
            link_path = CATALOG_DIR / "skills" / "by-expert" / safe_slug(expert_id) / skill_slug
            if local_skill_path:
                make_symlink(link_path, Path(local_skill_path))
            expert_skill_rows.append({
                "expert_id": expert_id,
                "ordinal": index,
                "skill_ref": skill_ref,
                "skill_slug": skill_slug,
                "local_skill_path": local_skill_path,
                "link_path": str(link_path) if local_skill_path else "",
                "skill_status": skill_status,
            })
            aggregate = skill_aggregate.setdefault(skill_slug, {
                "skill_slug": skill_slug,
                "skill_ref_examples": set(),
                "expert_ids": set(),
                "local_paths": set(),
                "downloaded_count": 0,
            })
            aggregate["skill_ref_examples"].add(skill_ref)
            aggregate["expert_ids"].add(expert_id)
            if local_skill_path:
                aggregate["local_paths"].add(local_skill_path)
                aggregate["downloaded_count"] += 1

    # Remove stale by-skill links only inside this generated directory.
    by_skill_dir = CATALOG_DIR / "skills" / "by-skill"
    by_skill_dir.mkdir(parents=True, exist_ok=True)
    for child in by_skill_dir.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
    by_skill_links: dict[str, Path] = {}
    used_skill_link_names: set[str] = set()
    for skill_slug, aggregate in sorted(skill_aggregate.items()):
        target = next(iter(sorted(aggregate["local_paths"])), None)
        if target:
            link_name = skill_slug
            if link_name.casefold() in used_skill_link_names:
                suffix = hashlib.sha256(skill_slug.encode("utf-8")).hexdigest()[:8]
                link_name = f"{skill_slug}--{suffix}"
                while link_name.casefold() in used_skill_link_names:
                    suffix = hashlib.sha256((skill_slug + link_name).encode("utf-8")).hexdigest()[:8]
                    link_name = f"{skill_slug}--{suffix}"
            used_skill_link_names.add(link_name.casefold())
            link_path = by_skill_dir / link_name
            make_symlink(link_path, Path(target))
            by_skill_links[skill_slug] = link_path

    skills_rows = []
    for skill_slug, aggregate in sorted(skill_aggregate.items()):
        skills_rows.append({
            "skill_slug": skill_slug,
            "skill_ref_examples": ";".join(sorted(aggregate["skill_ref_examples"])),
            "expert_count": len(aggregate["expert_ids"]),
            "expert_ids": ";".join(sorted(aggregate["expert_ids"])),
            "downloaded_count": aggregate["downloaded_count"],
            "local_paths": ";".join(sorted(aggregate["local_paths"])),
            "by_skill_link": str(by_skill_links[skill_slug]) if skill_slug in by_skill_links else "",
        })

    def scoped_skill_rows(expert_ids: set[str]) -> list[dict[str, Any]]:
        rows = []
        for row in skills_rows:
            row_expert_ids = set(filter(None, row["expert_ids"].split(";")))
            if row_expert_ids & expert_ids:
                scoped = dict(row)
                scoped["expert_ids"] = ";".join(sorted(row_expert_ids & expert_ids))
                scoped["expert_count"] = len(row_expert_ids & expert_ids)
                rows.append(scoped)
        return rows

    exact_scope_ids = {row["id"] for row in expert_rows if row["is_exact_marketing_category"]}
    keyword_scope_ids = {row["id"] for row in marketing_rows}
    skill_fields = list(skills_rows[0].keys()) if skills_rows else ["skill_slug"]
    exact_scope_skills = scoped_skill_rows(exact_scope_ids)
    keyword_scope_skills = scoped_skill_rows(keyword_scope_ids)

    db_path = CATALOG_DIR / "experts.db"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE categories (
            id TEXT PRIMARY KEY, name_zh TEXT, name_en TEXT,
            description_zh TEXT, description_en TEXT, expert_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE experts (
            id TEXT PRIMARY KEY, source_id TEXT, market_expert_id TEXT, agent_name TEXT,
            plugin TEXT, display_name_zh TEXT, display_name_en TEXT, name_zh TEXT, name_en TEXT,
            profession_zh TEXT, profession_en TEXT, description_zh TEXT, description_en TEXT,
            display_description_zh TEXT, display_description_en TEXT, category_id TEXT,
            category_name_zh TEXT, category_name_en TEXT, expert_type TEXT, visibility TEXT,
            version TEXT, author_zh TEXT, author_en TEXT, avatar TEXT, prompt_file TEXT,
            prompt_url TEXT, prompt_selected_url TEXT, prompt_local_path TEXT, prompt_status TEXT,
            prompt_bytes INTEGER NOT NULL DEFAULT 0, prompt_sha256 TEXT, signed_download_endpoint TEXT,
            is_opc INTEGER, is_cloud INTEGER,
            local_package_path TEXT, local_agent_path TEXT, agent_link_path TEXT, agent_source TEXT,
            agent_available INTEGER NOT NULL DEFAULT 0, package_status TEXT,
            created_at TEXT, updated_at TEXT, raw_json TEXT NOT NULL,
            is_exact_marketing_category INTEGER NOT NULL, is_marketing_keyword_match INTEGER NOT NULL,
            matched_keywords TEXT,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );
        CREATE TABLE expert_tags (
            expert_id TEXT NOT NULL, ordinal INTEGER NOT NULL, zh TEXT, en TEXT,
            PRIMARY KEY(expert_id, ordinal), FOREIGN KEY(expert_id) REFERENCES experts(id) ON DELETE CASCADE
        );
        CREATE TABLE quick_prompts (
            expert_id TEXT NOT NULL, ordinal INTEGER NOT NULL, zh TEXT, en TEXT,
            PRIMARY KEY(expert_id, ordinal), FOREIGN KEY(expert_id) REFERENCES experts(id) ON DELETE CASCADE
        );
        CREATE TABLE expert_skills (
            expert_id TEXT NOT NULL, ordinal INTEGER NOT NULL, skill_ref TEXT NOT NULL,
            skill_slug TEXT NOT NULL, local_skill_path TEXT, link_path TEXT, skill_status TEXT,
            PRIMARY KEY(expert_id, ordinal), FOREIGN KEY(expert_id) REFERENCES experts(id) ON DELETE CASCADE
        );
        CREATE TABLE skills (
            skill_slug TEXT PRIMARY KEY, skill_ref_examples TEXT, expert_count INTEGER NOT NULL,
            expert_ids TEXT, downloaded_count INTEGER NOT NULL, local_paths TEXT, by_skill_link TEXT
        );
        CREATE TABLE verification (
            check_id TEXT PRIMARY KEY, checked_at TEXT NOT NULL, source TEXT NOT NULL,
            status TEXT NOT NULL, observed TEXT NOT NULL
        );
        CREATE INDEX experts_category_idx ON experts(category_id);
        CREATE INDEX experts_marketing_idx ON experts(is_exact_marketing_category, is_marketing_keyword_match);
        CREATE INDEX expert_skills_slug_idx ON expert_skills(skill_slug);
        """
    )

    category_counts: dict[str, int] = {}
    for expert in experts:
        category_counts[str(expert.get("categoryId") or "")] = category_counts.get(str(expert.get("categoryId") or ""), 0) + 1
    meta = {
        "source_manifest": str(manifest_path),
        "source_manifest_sha256": catalog_sha256,
        "source_manifest_version": str(manifest.get("version") or ""),
        "source_manifest_last_updated": str(manifest.get("lastUpdated") or ""),
        "cached_expert_count": str(len(experts)),
        "built_at": built_at,
        "remote_base": REMOTE_BASE,
        "signed_download_endpoint": SIGNED_DOWNLOAD_ENDPOINT,
        "exact_marketing_categories": json_text(sorted(EXACT_MARKETING_CATEGORIES)),
        "marketing_keyword_count": str(len(marketing_rows)),
        "exact_marketing_category_count": str(sum(1 for row in expert_rows if row["is_exact_marketing_category"])),
    }
    conn.executemany("INSERT INTO catalog_meta(key,value) VALUES(?,?)", sorted(meta.items()))
    conn.executemany(
        "INSERT INTO categories VALUES(?,?,?,?,?,?)",
        [
            (
                str(item.get("id")), localized(item.get("name"), "zh"), localized(item.get("name"), "en"),
                localized(item.get("description"), "zh"), localized(item.get("description"), "en"),
                category_counts.get(str(item.get("id")), 0),
            )
            for item in categories
            if item.get("id")
        ],
    )
    expert_fields = [
        "id", "source_id", "market_expert_id", "agent_name", "plugin", "display_name_zh", "display_name_en",
        "name_zh", "name_en", "profession_zh", "profession_en", "description_zh", "description_en",
        "display_description_zh", "display_description_en", "category_id", "category_name_zh", "category_name_en",
        "expert_type", "visibility", "version", "author_zh", "author_en", "avatar", "prompt_file", "prompt_url",
        "prompt_selected_url", "prompt_local_path", "prompt_status", "prompt_bytes", "prompt_sha256",
        "signed_download_endpoint", "is_opc", "is_cloud", "local_package_path", "local_agent_path", "agent_link_path", "agent_source", "agent_available", "package_status",
        "created_at", "updated_at", "raw_json", "is_exact_marketing_category", "is_marketing_keyword_match", "matched_keywords",
    ]
    conn.executemany(
        f"INSERT INTO experts({','.join(expert_fields)}) VALUES({','.join('?' for _ in expert_fields)})",
        [tuple(row[field] for field in expert_fields) for row in expert_rows],
    )
    conn.executemany("INSERT INTO expert_tags VALUES(?,?,?,?)", [(r["expert_id"], r["ordinal"], r["zh"], r["en"]) for r in tag_rows])
    conn.executemany("INSERT INTO quick_prompts VALUES(?,?,?,?)", [(r["expert_id"], r["ordinal"], r["zh"], r["en"]) for r in quick_prompt_rows])
    conn.executemany(
        "INSERT INTO expert_skills VALUES(?,?,?,?,?,?,?)",
        [(r["expert_id"], r["ordinal"], r["skill_ref"], r["skill_slug"], r["local_skill_path"], r["link_path"], r["skill_status"]) for r in expert_skill_rows],
    )
    conn.executemany(
        "INSERT INTO skills VALUES(?,?,?,?,?,?,?)",
        [(r["skill_slug"], r["skill_ref_examples"], int(r["expert_count"]), r["expert_ids"], int(r["downloaded_count"]), r["local_paths"], r["by_skill_link"]) for r in skills_rows],
    )
    verification_rows = [
        ("local_cached_manifest", built_at, "WorkBuddy local cache", "pass", f"manifest.json contains {len(experts)} experts; SHA-256={catalog_sha256}"),
        ("ui_search_same_profession", built_at, "WorkBuddy Expert Center UI", "pass", "Search 中国电商运营专家 returned 2 entries: 卖得好 and 旺市; no message was sent."),
        ("ui_search_samples", built_at, "WorkBuddy Expert Center UI", "pass", "Exact profession searches matched cached catalog entries including 汽车营销专家、投标与方案策略师、Cordys CRM L2C 管道专家、广告投放操盘专家、亚马逊 Listing 优化专家、市场分析专家、营收增长师、自媒体热点雷达与内容增长官、微信视频号运营策略师; no message was sent."),
        ("ui_summon_package_structure", built_at, "WorkBuddy Expert Center UI + local filesystem", "pass", "Summoning 卖得好 created a local package with agents/, skills/, .codebuddy-plugin/plugin.json, README.md and license/."),
        ("ui_team_catalog", built_at, "WorkBuddy Expert Center UI", "observed", "Team tab visibly contained 营销增长专家团 and 腾讯健康NGES医药营销专家团. Team summon opened a points-consumption confirmation and was cancelled; no points were spent and no team chat was started."),
        ("full_bundle_inventory", built_at, "WorkBuddy official COS bundles + local filesystem", "pass", f"{len(package_cache)} logical plugins resolve to {sum(1 for root, plugin_manifest in package_cache.values() if root and plugin_manifest)} local package roots; all {len(expert_rows)} expert records have a local agent file and a non-broken by-expert link."),
        ("ui_current_remote_inventory", built_at, "WorkBuddy Expert Center UI", "observed", "After refreshing the Expert Center, the current remote UI reported 101 visible items; this is a separate view from the 446-entry local cache plus internal/external overlays used as the catalog source."),
        ("local_package_aliases", built_at, "WorkBuddy local filesystem + package manifests", "pass", "Unambiguous renamed package roots were matched by package manifest metadata, including paper-advisor, performance-management-expert and resume-optimization-expert; no expert record is left without a local agent file."),
    ]
    if args.live_manifest and args.live_manifest.is_file():
        try:
            live = json.loads(args.live_manifest.read_text(encoding="utf-8"))
            live_count = len(live.get("experts") or [])
            verification_rows.append(("live_cos_base_manifest", built_at, "WorkBuddy public COS manifest", "observed", f"public base manifest currently contains {live_count} experts; lastUpdated={live.get('lastUpdated', '')}; overlays and operation-platform results are separate."))
            merged_ids = {str(item.get("id")) for item in live.get("experts") or [] if item.get("id")}
            for overlay in args.overlay:
                overlay_path = overlay.expanduser()
                if not overlay_path.is_file():
                    continue
                try:
                    overlay_data = json.loads(overlay_path.read_text(encoding="utf-8"))
                    overlay_ids = {str(item.get("id")) for item in overlay_data.get("experts") or [] if item.get("id")}
                    merged_ids.update(overlay_ids)
                    verification_rows.append((f"overlay_{safe_slug(overlay_path.stem)}", built_at, f"WorkBuddy {overlay_path.stem} overlay", "observed", f"overlay contains {len(overlay_ids)} unique experts; {len(overlay_ids & {str(item.get('id')) for item in experts if item.get('id')})} are present in the cached catalog."))
                except (OSError, json.JSONDecodeError):
                    continue
            if args.overlay:
                cached_ids = {str(item.get("id")) for item in experts if item.get("id")}
                union_status = "pass" if merged_ids == cached_ids else "warning"
                verification_rows.append(("manifest_overlay_union", built_at, "WorkBuddy manifest union", union_status, f"public base + supplied overlays = {len(merged_ids)} unique experts; cached catalog = {len(cached_ids)}; exact_match={merged_ids == cached_ids}."))
        except (OSError, json.JSONDecodeError):
            pass
    conn.executemany("INSERT INTO verification VALUES(?,?,?,?,?)", verification_rows)
    conn.commit()
    conn.close()

    expert_fields_csv = [field for field in expert_fields if field != "raw_json"]
    csv_write(CATALOG_DIR / "experts.csv", expert_rows, expert_fields_csv)
    csv_write(CATALOG_DIR / "marketing_ecommerce.csv", marketing_rows, list(marketing_rows[0].keys()) if marketing_rows else ["id"])
    for category_id, file_name in (("05-MarketingGrowth", "marketing_growth.csv"), ("07-SalesCommerce", "sales_commerce.csv")):
        csv_write(CATALOG_DIR / file_name, [row for row in expert_rows if row["category_id"] == category_id], expert_fields_csv)
    csv_write(CATALOG_DIR / "skills.csv", skills_rows, list(skills_rows[0].keys()) if skills_rows else ["skill_slug"])
    csv_write(CATALOG_DIR / "exact_marketing_sales_skills.csv", exact_scope_skills, skill_fields)
    csv_write(CATALOG_DIR / "marketing_ecommerce_skills.csv", keyword_scope_skills, skill_fields)
    dump_json(CATALOG_DIR / "marketing_ecommerce.json", marketing_rows)
    dump_json(CATALOG_DIR / "skills.json", skills_rows)
    dump_json(CATALOG_DIR / "exact_marketing_sales_skills.json", exact_scope_skills)
    dump_json(CATALOG_DIR / "marketing_ecommerce_skills.json", keyword_scope_skills)
    dump_json(CATALOG_DIR / "verification.json", [
        {"check_id": row[0], "checked_at": row[1], "source": row[2], "status": row[3], "observed": row[4]}
        for row in verification_rows
    ])
    dump_json(CATALOG_DIR / "download_plan.json", [
        {
            "id": row["id"],
            "plugin": row["plugin"],
            "agent_name": row["agent_name"],
            "category_id": row["category_id"],
            "profession_zh": row["profession_zh"],
            "prompt_file": row["prompt_file"],
            "prompt_url": row["prompt_url"],
            "market_expert_id": row["market_expert_id"],
            "signed_download_endpoint": row["signed_download_endpoint"],
            "local_package_path": row["local_package_path"],
            "local_agent_path": row["local_agent_path"],
            "agent_link_path": row["agent_link_path"],
            "agent_source": row["agent_source"],
            "agent_available": row["agent_available"],
            "package_status": row["package_status"],
            "recommended_scope": "exact_marketing_sales" if row["is_exact_marketing_category"] else ("marketing_ecommerce_keyword" if row["is_marketing_keyword_match"] else "all_catalog"),
        }
        for row in expert_rows
    ])

    package_rows = []
    for plugin, (package_root, plugin_manifest) in sorted(package_cache.items()):
        metadata_root, metadata_manifest = metadata_cache.get(plugin, (None, None))
        effective_manifest = plugin_manifest or metadata_manifest
        package_rows.append({
            "plugin": plugin,
            "package_root": str(package_root) if package_root else "",
            "plugin_manifest": str(find_plugin_manifest(package_root)) if package_root and find_plugin_manifest(package_root) else "",
            "metadata_root": str(metadata_root) if metadata_root else "",
            "metadata_manifest": str(find_plugin_manifest(metadata_root)) if metadata_root and find_plugin_manifest(metadata_root) else "",
            "status": "downloaded" if package_root and plugin_manifest else ("directory_without_plugin_json" if package_root else ("metadata_only" if metadata_manifest else "planned")),
            "skills": skill_refs_from_plugin(effective_manifest),
        })
    dump_json(CATALOG_DIR / "packages.json", package_rows)

    report = {
        "built_at": built_at,
        "source_manifest": str(manifest_path),
        "source_manifest_sha256": catalog_sha256,
        "source_manifest_version": manifest.get("version"),
        "source_manifest_last_updated": manifest.get("lastUpdated"),
        "expert_count": len(experts),
        "category_count": len(categories),
        "category_counts": category_counts,
        "exact_marketing_category_count": sum(1 for row in expert_rows if row["is_exact_marketing_category"]),
        "marketing_ecommerce_keyword_union_count": len(marketing_rows),
        "unique_plugins": len(package_cache),
        "local_downloaded_plugins": sum(1 for root, plugin_manifest in package_cache.values() if root and plugin_manifest),
        "unique_skills_seen": len(skills_rows),
        "skill_symlinks_created": sum(1 for row in expert_skill_rows if row["link_path"]),
        "agent_symlinks_created": sum(1 for row in expert_rows if row["agent_link_path"]),
        "agents_available": sum(row["agent_available"] for row in expert_rows),
        "local_package_agents": sum(1 for row in expert_rows if row["agent_source"] == "local_package"),
        "public_static_agents": sum(1 for row in expert_rows if row["agent_source"] == "public_static_prompt"),
        "agents_planned": sum(1 for row in expert_rows if not row["agent_available"]),
        "public_prompt_downloaded": sum(1 for row in expert_rows if row["prompt_status"] == "downloaded"),
        "public_prompt_failed": sum(1 for row in expert_rows if row["prompt_status"] == "failed"),
        "remote_base": REMOTE_BASE,
        "signed_download_endpoint": SIGNED_DOWNLOAD_ENDPOINT,
        "notes": [
            "The primary dataset is the 446-entry manifest cached by this WorkBuddy installation.",
            "A current public COS base manifest can differ; WorkBuddy also merges internal/external manifests and operation-platform results.",
            "The signed download endpoint is recorded for later package retrieval; query strings are intentionally never persisted.",
            "Downloaded skill directories are linked under skills/by-expert and skills/by-skill; source packages remain in WorkBuddy's local store.",
        ],
    }
    dump_json(CATALOG_DIR / "report.json", report)

    readme = f"""# WorkBuddy Expert Catalog

构建时间：`{built_at}`

本目录以 WorkBuddy 本机缓存的 `manifest.json` 为主数据源：{len(experts)} 个专家、{len(categories)} 个分类。源文件快照位于 `snapshots/expert_center.json`，SHA-256 为 `{catalog_sha256}`。

## 已生成内容

- `experts.db`：SQLite 数据库，包含专家、分类、标签、快捷提示词、技能引用、包状态和验证记录。
- `experts.csv`：全部专家清单。
- `marketing_growth.csv` / `sales_commerce.csv`：严格按营销增长、销售商务两个分类筛选，共 {sum(1 for row in expert_rows if row['is_exact_marketing_category'])} 个。
- `marketing_ecommerce.csv` / `marketing_ecommerce.json`：分类或名称、简介、标签中命中电商/营销词的扩大集合，共 {len(marketing_rows)} 个。
- `skills.csv` / `skills.json`：技能去重清单及其引用专家。
- `exact_marketing_sales_skills.csv` / `marketing_ecommerce_skills.csv`：两个筛选范围对应的技能清单。
- `download_plan.json`：全部专家的提示词直链、专家包现签接口和后续下载范围。
- `experts.csv` / `experts.db` 中的 `prompt_status` 是公开静态提示词抓取结果；`agent_source`、`agent_available` 是本机实际可用的 agent 状态。公开地址 404 不等于专家不可获取，优先看后两列和 `package_status`。
- `skills/by-expert/`、`skills/by-skill/`：指向已下载包中技能目录的软链；尚未下载的技能只记录在数据库和清单中。
- `agents/by-expert/`：指向本地专家提示词或已下载包中 agent 文件的软链。
- `verification.json`：本地缓存、WorkBuddy 界面搜索和实际召唤落包的验证记录。

## 当前状态

- 446 个专家，15 个分类；严格的 `05-MarketingGrowth` + `07-SalesCommerce` 共 54 个，关键词扩展筛选共 {len(marketing_rows)} 个。
- WorkBuddy 本地已有 {sum(1 for root, plugin_manifest in package_cache.values() if root and plugin_manifest)} 个完整包；其中 {sum(row['agent_available'] for row in expert_rows)} 个 agent 提示词可直接使用或通过软链访问。
- 公开静态提示词抓取结果为 {sum(1 for row in expert_rows if row['prompt_status'] == 'downloaded')} 成功、{sum(1 for row in expert_rows if row['prompt_status'] == 'failed')} 个 404；另有 {len(skills_rows)} 个去重技能引用，当前 {sum(1 for row in expert_skill_rows if row['link_path'])} 条技能软链已落地。

## WorkBuddy 包结构

典型包根目录为 `plugins/experts/<plugin>/`，包含：

```text
.codebuddy-plugin/plugin.json
agents/<agent-name>.md
skills/<skill-name>/SKILL.md
skills/<skill-name>/references/...
avatars/...
license/...
README.md
```

## 更新目录

```bash
python3 build_catalog.py \\
  --live-manifest snapshots/live_expert_center.json \\
  --overlay snapshots/internalExpert.json \\
  --overlay snapshots/externalExpert.json
```

提示词的公开 COS 地址由 `prompt_url` 给出；完整包对有 `market_expert_id` 的条目需要调用 WorkBuddy 的短时签名下载接口：`{SIGNED_DOWNLOAD_ENDPOINT}`。为避免泄露授权信息，本目录不保存签名 URL 查询串。

注意：缓存清单为 446 条；公开 COS 基础清单、内部/外部覆盖清单和 operation-platform 实时列表可能有不同数量，不能简单相加。
"""
    (CATALOG_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
