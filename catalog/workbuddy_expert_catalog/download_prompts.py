#!/usr/bin/env python3
"""Download raw public WorkBuddy agent prompts from the local expert manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urljoin

from build_catalog import (
    CATALOG_DIR,
    DEFAULT_MANIFEST,
    EXACT_MARKETING_CATEGORIES,
    MARKETING_KEYWORDS,
    REMOTE_BASE,
    localized,
    safe_slug,
)

USER_AGENT = "WorkBuddyExpertCatalog/1.0"
TIMEOUT_SECONDS = 45
MAX_BYTES = 32 * 1024 * 1024


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(flatten_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(flatten_strings(item))
        return out
    return []


def candidate_urls(expert: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    prompt_file = str(expert.get("promptFile") or "").strip()
    if prompt_file:
        urls.append(urljoin(REMOTE_BASE + "/", prompt_file.lstrip("/")))
    plugin = str(expert.get("plugin") or expert.get("agentName") or "").strip()
    agent_name = str(expert.get("agentName") or "").strip()
    if plugin and agent_name:
        fallback = urljoin(REMOTE_BASE + "/", f"plugins/{plugin}/agents/{agent_name}.md")
        if fallback not in urls:
            urls.append(fallback)
    return urls


def local_path(expert: dict[str, Any], url: str) -> Path:
    expert_id = safe_slug(str(expert.get("id") or expert.get("agentName") or "expert"))
    filename = Path(str(expert.get("promptFile") or "")).name
    if not filename:
        filename = Path(url.split("?", 1)[0]).name
    if not filename:
        filename = f"{safe_slug(str(expert.get('agentName') or expert_id))}.md"
    return CATALOG_DIR / "prompts" / expert_id / filename


def fetch_one(expert: dict[str, Any]) -> dict[str, Any]:
    expert_id = str(expert.get("id") or expert.get("agentName") or "")
    urls = candidate_urls(expert)
    result: dict[str, Any] = {
        "id": expert_id,
        "plugin": expert.get("plugin") or "",
        "agent_name": expert.get("agentName") or "",
        "display_name_zh": localized(expert.get("displayName"), "zh"),
        "profession_zh": localized(expert.get("profession"), "zh"),
        "category_id": expert.get("categoryId") or "",
        "prompt_file": expert.get("promptFile") or "",
        "candidate_urls": urls,
        "selected_url": "",
        "local_path": "",
        "status": "missing_source_path" if not urls else "failed",
        "http_status": "",
        "bytes": 0,
        "sha256": "",
        "error": "",
    }
    if not urls:
        result["error"] = "no promptFile and no plugin/agentName fallback"
        return result

    for url in urls:
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/markdown,*/*"})
            with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                body = response.read(MAX_BYTES + 1)
                status = getattr(response, "status", 200)
            if len(body) > MAX_BYTES:
                raise ValueError(f"response exceeds {MAX_BYTES} bytes")
            if not 200 <= status < 300:
                raise HTTPError(url, status, f"HTTP {status}", None, None)
            destination = local_path(expert, url)
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(prefix=".prompt-", suffix=".tmp", dir=destination.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(body)
                os.replace(temporary_name, destination)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)
            result.update({
                "selected_url": url,
                "local_path": str(destination),
                "status": "downloaded",
                "http_status": status,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "error": "",
            })
            return result
        except HTTPError as exc:
            result["http_status"] = exc.code
            result["error"] = f"HTTP {exc.code}"
        except (OSError, URLError, ValueError) as exc:
            result["error"] = str(exc)
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def selected(expert: dict[str, Any], scope: str) -> bool:
    if scope == "all":
        return True
    category_id = str(expert.get("categoryId") or "")
    if scope == "exact_marketing_sales":
        return category_id in EXACT_MARKETING_CATEGORIES
    if scope == "marketing_ecommerce":
        text = " ".join(flatten_strings(expert)).casefold()
        return category_id in EXACT_MARKETING_CATEGORIES or any(keyword.casefold() in text for keyword in MARKETING_KEYWORDS)
    raise ValueError(scope)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--scope", choices=("all", "exact_marketing_sales", "marketing_ecommerce"), default="all")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    experts = [item for item in (manifest.get("experts") or []) if selected(item, args.scope)]
    if not experts:
        raise SystemExit("no experts selected")

    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results: list[dict[str, Any]] = []
    workers = max(1, min(int(args.workers), 32))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_one, expert) for expert in experts]
        for future in as_completed(futures):
            results.append(future.result())
            if len(results) % 25 == 0 or len(results) == len(experts):
                print(f"fetched {len(results)}/{len(experts)}", flush=True)
    results.sort(key=lambda row: row["id"])

    report = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "manifest": str(manifest_path),
        "manifest_last_updated": manifest.get("lastUpdated") or "",
        "manifest_expert_count": len(manifest.get("experts") or []),
        "selected_scope": args.scope,
        "selected_count": len(experts),
        "downloaded_count": sum(row["status"] == "downloaded" for row in results),
        "failed_count": sum(row["status"] != "downloaded" for row in results),
        "remote_base": REMOTE_BASE,
    }
    output_json = CATALOG_DIR / "prompt_fetch_results.json"
    output_csv = CATALOG_DIR / "prompt_fetch_results.csv"
    dump_json(output_json, {"report": report, "results": results})
    fields = ["id", "plugin", "agent_name", "display_name_zh", "profession_zh", "category_id", "prompt_file", "selected_url", "local_path", "status", "http_status", "bytes", "sha256", "error"]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    readme = f"""# WorkBuddy Agent Prompts

原始 Markdown 提示词来自 WorkBuddy Expert Center 的公开 COS 资源。

- 清单：`{manifest_path}`
- 清单更新时间：`{manifest.get('lastUpdated', '')}`
- 范围：`{args.scope}`，{len(experts)} 条
- 成功：{report['downloaded_count']}；失败：{report['failed_count']}
- 明细和 SHA-256：`prompt_fetch_results.csv` / `prompt_fetch_results.json`

文件按 `prompts/<expert-id>/<原始文件名>` 保存，正文未改写。缺少 `promptFile`
的条目会额外尝试 `/plugins/<plugin>/agents/<agentName>.md` 约定路径。
"""
    (CATALOG_DIR / "prompts" / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
