#!/usr/bin/env python3
"""Offline search and extraction tools for the bundled agent-remix library.

The command is intentionally standard-library-only. The language model performs
the actual prompt synthesis; this helper makes source selection, inspection, and
portable extraction deterministic.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_index() -> tuple[Path, dict[str, Any]]:
    root = skill_root()
    index_path = root / "library" / "index.json"
    if not index_path.is_file():
        raise RuntimeError(
            f"bundled library is missing: {index_path}. "
            "Run scripts/build_library.py while maintaining the source catalog."
        )
    try:
        return root, json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read bundled index: {index_path}: {exc}") from exc


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", compact(value).lower()).strip()


def query_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9._-]*|[\u3400-\u9fff]+", query.lower())
    return [token for token in tokens if token]


def agent_title(agent: dict[str, Any]) -> str:
    return (
        compact(agent.get("name_zh"))
        or compact(agent.get("name_en"))
        or compact(agent.get("role_stem"))
        or compact(agent.get("agent_id"))
    )


def agent_skill_slugs(agent: dict[str, Any]) -> list[str]:
    return sorted(
        {
            compact(binding.get("skill_slug"))
            for binding in agent.get("skills", [])
            if compact(binding.get("skill_slug"))
        }
    )


def agent_search_text(agent: dict[str, Any]) -> str:
    fields = (
        "agent_id",
        "name_zh",
        "name_en",
        "description_zh",
        "description_en",
        "category_raw",
        "domain_id",
        "subcategory",
        "role_stem",
        "family_key",
        "family_label_zh",
        "family_label_en",
        "topic_tags",
        "plugin",
    )
    values = [compact(agent.get(field)) for field in fields]
    values.extend(agent_skill_slugs(agent))
    return normalize(" ".join(values))


def skill_search_text(skill: dict[str, Any]) -> str:
    return normalize(
        " ".join(
            [
                compact(skill.get("skill_slug")),
                compact(skill.get("source_ids")),
                compact(skill.get("source_paths")),
            ]
        )
    )


def score_match(query: str, text: str, title: str = "") -> int:
    query_norm = normalize(query)
    if not query_norm:
        return 0
    score = 0
    if query_norm in text:
        score += 8
    title_norm = normalize(title)
    if title_norm and query_norm in title_norm:
        score += 8
    for token in query_tokens(query):
        if token in text:
            score += 4
        if token and token in title_norm:
            score += 5
    return score


def public_agent(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": agent.get("agent_id"),
        "title": agent_title(agent),
        "name_zh": agent.get("name_zh"),
        "name_en": agent.get("name_en"),
        "description_zh": agent.get("description_zh"),
        "description_en": agent.get("description_en"),
        "source_type": agent.get("source_type"),
        "source_repo": agent.get("source_repo"),
        "source_commit": agent.get("source_commit"),
        "source_path": agent.get("source_path"),
        "domain_id": agent.get("domain_id"),
        "category_raw": agent.get("category_raw"),
        "family_label_zh": agent.get("family_label_zh"),
        "family_label_en": agent.get("family_label_en"),
        "topic_tags": agent.get("topic_tags"),
        "bundle_path": agent.get("bundle_path"),
        "skills": agent_skill_slugs(agent),
    }


def public_skill(skill: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_slug": skill.get("skill_slug"),
        "cataloged": skill.get("cataloged"),
        "unbound_source": skill.get("unbound_source", False),
        "expert_count": skill.get("expert_count"),
        "downloaded_count": skill.get("downloaded_count"),
        "source_ids": skill.get("source_ids"),
        "source_paths": skill.get("source_paths"),
        "selected_source_path": skill.get("selected_source_path"),
        "bundle_path": skill.get("bundle_path"),
        "bundle_files": skill.get("bundle_files", []),
        "excluded_files": skill.get("excluded_files", []),
        "status": skill.get("status"),
    }


def find_agent(index: dict[str, Any], identifier: str) -> dict[str, Any]:
    needle = normalize(identifier)
    agents = index.get("agents", [])
    exact_fields = ("agent_id", "name_zh", "name_en", "role_stem")
    for agent in agents:
        if any(normalize(agent.get(field)) == needle for field in exact_fields):
            return agent
    for agent in agents:
        if normalize(agent.get("bundle_path")).endswith("/" + needle):
            return agent
        if Path(compact(agent.get("source_path"))).stem.lower() == needle:
            return agent
    raise KeyError(f"agent not found: {identifier}")


def find_skill(index: dict[str, Any], slug: str) -> dict[str, Any]:
    needle = normalize(slug)
    for skill in index.get("skills", []):
        if normalize(skill.get("skill_slug")) == needle:
            return skill
    raise KeyError(f"skill not found: {slug}")


def safe_library_path(root: Path, relative: str) -> Path:
    candidate = (root / "library" / relative).resolve()
    library = (root / "library").resolve()
    try:
        candidate.relative_to(library)
    except ValueError as exc:
        raise RuntimeError(f"index path escapes bundled library: {relative}") from exc
    return candidate


def cmd_stats(index: dict[str, Any], as_json: bool) -> int:
    result = {
        "package": index.get("package", "agent-remix"),
        "self_contained": bool(index.get("self_contained")),
        "counts": index.get("counts", {}),
        "generated_at": index.get("generated_at"),
        "network_used": index.get("build_policy", {}).get("network_used", False),
    }
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    counts = result["counts"]
    print(f"package: {result['package']}")
    print(f"self-contained: {result['self_contained']}")
    print(f"agents: {counts.get('agents', 0)}")
    print(f"catalog skills: {counts.get('catalog_skills', 0)}")
    print(f"bundled skills: {counts.get('skills', 0)}")
    print(f"agent-skill bindings: {counts.get('bindings', 0)}")
    print(f"missing records: {counts.get('missing_records', 0)}")
    print(f"network used to build: {result['network_used']}")
    return 0


def cmd_search(index: dict[str, Any], args: argparse.Namespace) -> int:
    results: list[tuple[int, str, dict[str, Any]]] = []
    kinds = {"agents", "skills"} if args.kind == "all" else {args.kind}
    if "agents" in kinds:
        for agent in index.get("agents", []):
            score = score_match(args.query, agent_search_text(agent), agent_title(agent))
            if score:
                results.append((score, "agent", public_agent(agent)))
    if "skills" in kinds:
        for skill in index.get("skills", []):
            score = score_match(
                args.query, skill_search_text(skill), compact(skill.get("skill_slug"))
            )
            if score:
                results.append((score, "skill", public_skill(skill)))
    results.sort(
        key=lambda item: (-item[0], item[1], compact(item[2].get("agent_id") or item[2].get("skill_slug")))
    )
    results = results[: args.limit]
    if args.json:
        print(
            json.dumps(
                [
                    {"kind": kind, "score": score, **record}
                    for score, kind, record in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if not results:
        print("No matches.")
        return 0
    for score, kind, record in results:
        if kind == "agent":
            title = record["title"]
            identifier = record["agent_id"]
            description = record.get("description_zh") or record.get("description_en") or ""
            skill_text = ", ".join(record.get("skills", []))
            print(f"[agent] {title}  ({identifier})  score={score}")
            if description:
                print(f"  {description}")
            if skill_text:
                print(f"  skills: {skill_text}")
        else:
            print(
                f"[skill] {record['skill_slug']}  "
                f"experts={record.get('expert_count', 0)}  score={score}"
            )
    return 0


def cmd_show_agent(root: Path, index: dict[str, Any], identifier: str) -> int:
    agent = find_agent(index, identifier)
    bundle_path = compact(agent.get("bundle_path"))
    prompt_path = safe_library_path(root, bundle_path)
    if not prompt_path.is_file():
        raise RuntimeError(f"bundled prompt is missing: {bundle_path}")
    print(json.dumps(public_agent(agent), ensure_ascii=False, indent=2))
    print("\n--- PROMPT ---\n")
    print(prompt_path.read_text(encoding="utf-8", errors="replace"))
    return 0


def cmd_show_skill(
    root: Path, index: dict[str, Any], slug: str, list_files: bool
) -> int:
    skill = find_skill(index, slug)
    bundle_path = compact(skill.get("bundle_path"))
    skill_dir = safe_library_path(root, bundle_path)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise RuntimeError(f"bundled SKILL.md is missing: {bundle_path}")
    print(json.dumps(public_skill(skill), ensure_ascii=False, indent=2))
    print("\n--- SKILL.md ---\n")
    print(skill_md.read_text(encoding="utf-8", errors="replace"))
    if list_files:
        print("\n--- BUNDLED SUPPORT FILES ---\n")
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                print(path.relative_to(skill_dir).as_posix())
    return 0


def cmd_extract_agent(
    root: Path, index: dict[str, Any], identifier: str, output_arg: str, force: bool
) -> int:
    agent = find_agent(index, identifier)
    output = Path(output_arg).expanduser().resolve()
    if output.exists():
        if not force and any(output.iterdir()):
            raise RuntimeError(f"output is not empty; pass --force to replace: {output}")
        if force:
            shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    prompt_path = safe_library_path(root, compact(agent.get("bundle_path")))
    if not prompt_path.is_file():
        raise RuntimeError("selected agent has no bundled prompt")
    shutil.copy2(prompt_path, output / "agent.md")

    selected_skills: list[dict[str, Any]] = []
    for binding in agent.get("skills", []):
        slug = compact(binding.get("skill_slug"))
        if not slug:
            continue
        skill = find_skill(index, slug)
        skill_dir = safe_library_path(root, compact(skill.get("bundle_path")))
        if not skill_dir.is_dir():
            raise RuntimeError(f"selected skill is not bundled: {slug}")
        destination = output / "skills" / slug
        shutil.copytree(skill_dir, destination, dirs_exist_ok=True)
        selected_skills.append(
            {
                "skill_slug": slug,
                "source_binding": binding,
                "bundle_path": skill.get("bundle_path"),
                "status": skill.get("status"),
                "excluded_files": skill.get("excluded_files", []),
            }
        )

    manifest = {
        "package": "agent-remix-extracted-agent",
        "agent": public_agent(agent),
        "skills": selected_skills,
        "portable": True,
        "network_used": False,
        "notes": [
            "This extraction copies materialized text and safe support files.",
            "Review each skill's excluded_files and local runtime notes before execution.",
        ],
    }
    (output / "provenance.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(output), "skills": len(selected_skills)}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and extract the bundled agent-remix library offline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats = subparsers.add_parser("stats", help="show bundled counts")
    stats.add_argument("--json", action="store_true")

    search = subparsers.add_parser("search", help="search agents and skills")
    search.add_argument("query")
    search.add_argument("--kind", choices=("all", "agents", "skills"), default="all")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true")

    show_agent = subparsers.add_parser("show-agent", help="print metadata and full prompt")
    show_agent.add_argument("identifier")

    show_skill = subparsers.add_parser("show-skill", help="print a bundled skill")
    show_skill.add_argument("slug")
    show_skill.add_argument("--files", action="store_true", dest="list_files")

    extract = subparsers.add_parser(
        "extract-agent", help="copy an agent and its bundled skills"
    )
    extract.add_argument("identifier")
    extract.add_argument("--output", required=True)
    extract.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        root, index = load_index()
        if args.command == "stats":
            return cmd_stats(index, args.json)
        if args.command == "search":
            if args.limit < 1:
                raise RuntimeError("--limit must be positive")
            return cmd_search(index, args)
        if args.command == "show-agent":
            return cmd_show_agent(root, index, args.identifier)
        if args.command == "show-skill":
            return cmd_show_skill(root, index, args.slug, args.list_files)
        if args.command == "extract-agent":
            return cmd_extract_agent(root, index, args.identifier, args.output, args.force)
    except (KeyError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
