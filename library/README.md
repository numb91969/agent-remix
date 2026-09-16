# Bundled Agent Library

This directory is materialized by scripts/build_library.py and is shipped inside the
agent-remix skill. It is intentionally self-contained: normal search and extraction do
not fetch another repository.

- Agents: 1004
- Cataloged skills: 721
- Bundled skills, including locally discovered unbound skills: 971
- Agent-skill bindings: 929
- Missing or excluded source records: 0

Use index.json with scripts/agent_remix.py. Each agent and skill keeps its original
source repository, commit, relative source path, and content hash when that metadata was
available.
