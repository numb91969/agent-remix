---
name: agent-remix
description: Build a custom Codex or WorkBuddy agent by searching and combining the bundled 1000+ expert prompts and skills, with provenance and dependency review.
metadata:
  short-description: Self-contained expert remix library
---

# Agent Remix

This is a self-contained skill package. The bundled library under 'library/' contains the expert prompts and skill material needed for normal remix work. Do not fetch the source repositories or ask the user to download another catalog unless the user explicitly requests a refresh.

## What this skill does

- Searches the bundled catalog of 1004 expert agents and the bundled skill library.
- Combines multiple complementary experts instead of renaming or lightly editing one source.
- Produces a standalone system prompt, skill map, provenance record, and dependency decision.
- Supports Codex and WorkBuddy folder-based skill installation.
- Keeps external APIs, private MCPs, paid databases, credentials, absolute paths, and non-portable links out of a portable package.

## Bundled layout

~~~text
agent-remix/
├── SKILL.md
├── agents/openai.yaml
├── library/
│   ├── index.json       # agent/skill metadata and bindings
│   ├── agents/          # 1004 materialized expert prompt files
│   └── skills/          # bundled skill documents and safe support files
├── scripts/
│   ├── agent_remix.py   # search, inspect, and extract without network access
│   └── build_library.py # maintainer-only rebuild from a merged catalog
├── references/
└── examples/
~~~

'library/index.json' is the runtime catalog. It is deliberately JSON rather than a database so an installed copy works with Python's standard library and does not need SQLite, Node, or a connector.

## Runtime commands

Run these from this skill directory:

~~~sh
python3 scripts/agent_remix.py stats
python3 scripts/agent_remix.py search "财务 现金流"
python3 scripts/agent_remix.py search "读书 知识库" --kind all --limit 20
python3 scripts/agent_remix.py show-agent workbuddy:BookCoCreator
python3 scripts/agent_remix.py show-skill personal-knowledge-architect
python3 scripts/agent_remix.py extract-agent workbuddy:LlmWiki --output ./exports/llm-wiki
~~~

'search' is the normal entry point. Use 'show-agent' and 'show-skill' to inspect the full source text before remixing. 'extract-agent' copies the selected prompt and its bundled skills into a portable output directory; it does not create absolute symlinks or access the network.

## Remix workflow

1. Translate the target into capability clusters: identity, core duties, methods, outputs, risk controls, and integrations.
2. Search the local library by role, domain, description, and skill terms. Choose several complementary sources when the task needs more than one capability.
3. Read the full prompt and the relevant skill documents. Record each source agent, source path, source commit when available, retained material, and discarded material.
4. Write one coherent prompt:
   - Put a user-requested self-naming or identity restriction at the beginning.
   - Define the target identity, audience, authority limits, and escalation points.
   - Merge duplicate capabilities into a prioritized capability tree.
   - Convert source workflows into clear inputs, checks, outputs, and review loops.
   - Keep platform-specific commands out of the standalone prompt unless the target host supports them.
5. Audit every skill:
   - 'direct': self-contained text and local/common runtime only.
   - 'symlink-audit': use only as a local development relationship; materialize the skill text in any export.
   - 'exclude': external API, private MCP, paid or credentialed service, enterprise network, .NET or other unavailable runtime, absolute path, restricted license, or non-portable binary.
6. Deliver the final prompt, source evidence table, skill map, dependency decisions, and known limitations. Never claim that an agent was published, installed, or that an external action was completed unless it was actually verified.

## Dependency policy

The bundled files are available without another download, but a bundled skill can still describe a runtime dependency. Treat these separately:

- A local PDF/DOCX parser may be bundled as text while still requiring a local command or library.
- A web-search skill is not offline merely because it needs no API key.
- An agent that calls a vendor service, private data source, or token-protected endpoint is not portable; keep the prompt idea as a reference and exclude the integration.
- Do not copy secrets, cookies, session files, .env files, user home paths, or absolute symlinks.

For detailed source selection, dependency decisions, catalog fields, and export rules, read the relevant file in 'references/' only when that mode is needed.

## Codex and WorkBuddy installation

Download this repository once, then install or copy the repository root as the 'agent-remix/' skill folder. The expert library is inside that folder; normal use does not require another repository, API, or catalog download.

For Codex, place the folder at the configured skills directory, normally '~/.codex/skills/agent-remix/'. For WorkBuddy or another folder-based host, place the same folder in its local skills directory and keep the 'library/' directory beside 'SKILL.md'.

## Maintainer rebuild

Only rebuild the library when the source catalog is intentionally refreshed:

~~~sh
python3 scripts/build_library.py \
  --catalog /path/to/merged_catalog.db \
  --source-root /path/to/source/repository \
  --output ./library \
  --force
~~~

The rebuild uses Python's standard library, materializes relative files, records missing or excluded support files, and discovers unbound local 'SKILL.md' files so a prompt is not silently separated from its skill.

## Output contract

Every remix should leave a compact, reproducible record:

- final system prompt;
- source agents and the contribution from each;
- retained and discarded content;
- skill bindings and direct/symlink-audit/exclude decisions;
- external or local runtime prerequisites;
- validation and publication status, if publication was requested and verified.

Use the example under 'examples/' as a small reference for the expected output shape.
