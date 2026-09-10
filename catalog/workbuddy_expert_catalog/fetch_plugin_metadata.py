#!/usr/bin/env python3
"""Fetch public plugin.json files so the catalog can enumerate skill refs."""

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
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from build_catalog import CATALOG_DIR, DEFAULT_MANIFEST, REMOTE_BASE, safe_slug

USER_AGENT = "WorkBuddyExpertCatalog/1.0"


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def urls_for(plugin: str) -> list[tuple[str, str]]:
    return [
        ("codebuddy", urljoin(REMOTE_BASE + "/", f"plugins/{plugin}/.codebuddy-plugin/plugin.json")),
        ("workbuddy", urljoin(REMOTE_BASE + "/", f"plugins/{plugin}/.workbuddy-plugin/plugin.json")),
    ]


def fetch_one(plugin: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "plugin": plugin,
        "status": "failed",
        "selected_url": "",
        "local_path": "",
        "http_status": "",
        "bytes": 0,
        "sha256": "",
        "agent_refs": [],
        "skill_refs": [],
        "error": "",
    }
    for flavor, url in urls_for(plugin):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
            with urlopen(request, timeout=45) as response:
                body = response.read(8 * 1024 * 1024 + 1)
                status = getattr(response, "status", 200)
            if len(body) > 8 * 1024 * 1024:
                raise ValueError("plugin.json exceeds 8 MiB")
            if not 200 <= status < 300:
                raise HTTPError(url, status, f"HTTP {status}", None, None)
            data = json.loads(body.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("plugin.json is not an object")
            metadata_dir = CATALOG_DIR / "package_metadata" / safe_slug(plugin) / f".{flavor}-plugin"
            destination = metadata_dir / "plugin.json"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(prefix=".plugin-", suffix=".tmp", dir=metadata_dir)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(body)
                os.replace(temporary_name, destination)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)
            result.update({
                "status": "downloaded",
                "selected_url": url,
                "local_path": str(destination),
                "http_status": status,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "agent_refs": [item for item in data.get("agents", []) if isinstance(item, str)],
                "skill_refs": [item for item in data.get("skills", []) if isinstance(item, str)],
                "error": "",
            })
            return result
        except HTTPError as exc:
            result["http_status"] = exc.code
            result["error"] = f"HTTP {exc.code}"
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plugins: dict[str, dict[str, Any]] = {}
    for expert in manifest.get("experts") or []:
        plugin = str(expert.get("plugin") or expert.get("agentName") or "").strip()
        if plugin and plugin not in plugins:
            plugins[plugin] = expert
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(int(args.workers), 32))) as executor:
        futures = [executor.submit(fetch_one, plugin) for plugin in sorted(plugins)]
        for future in as_completed(futures):
            results.append(future.result())
            if len(results) % 25 == 0 or len(results) == len(futures):
                print(f"metadata {len(results)}/{len(futures)}", flush=True)
    results.sort(key=lambda row: row["plugin"])
    report = {
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "manifest": str(manifest_path),
        "manifest_expert_count": len(manifest.get("experts") or []),
        "unique_plugin_count": len(plugins),
        "downloaded_count": sum(row["status"] == "downloaded" for row in results),
        "failed_count": sum(row["status"] != "downloaded" for row in results),
        "plugins_with_skills": sum(bool(row["skill_refs"]) for row in results),
        "unique_skill_ref_count": len({ref for row in results for ref in row["skill_refs"]}),
        "remote_base": REMOTE_BASE,
    }
    dump_json(CATALOG_DIR / "plugin_metadata_results.json", {"report": report, "results": results})
    fields = ["plugin", "status", "selected_url", "local_path", "http_status", "bytes", "sha256", "agent_refs", "skill_refs", "error"]
    with (CATALOG_DIR / "plugin_metadata_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            output = dict(row)
            output["agent_refs"] = ";".join(row["agent_refs"])
            output["skill_refs"] = ";".join(row["skill_refs"])
            writer.writerow(output)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
