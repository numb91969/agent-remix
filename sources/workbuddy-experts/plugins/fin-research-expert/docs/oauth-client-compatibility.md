# OAuth Client Compatibility

The supported clients share one canonical MCP resource and one account/session model. Capability selection is explicit; no client receives four new server entries unless legacy mode is requested.

| Client class | Targets | Transport | Credential behavior |
|---|---|---|---|
| WorkBuddy Connector | WorkBuddy 5.0+ | Direct remote Streamable HTTP | Native browser OAuth with PKCE and a protected renewable session. |
| Direct remote OAuth | Claude Code, Cursor, VS Code/Copilot where supported | Remote `/mcp/tongzhou-research` | Client performs protected-resource discovery and OAuth. |
| Stdio OAuth proxy | Codex, Windsurf, OpenCode, Gemini CLI, Copilot CLI, Cline, Hermes Agent | Local npm stdio proxy to canonical remote MCP | npm CLI performs Device Flow and stores the renewable session in the OS credential backend. |
| Explicit legacy rollback | All previously supported targets | Four remote API-Key entries | Only with `--legacy-api-key`; old config is backed up and is not revoked automatically. |

## Verified Locally

- npm Device Flow, status, logout, refresh lock, proxy initialize/list/call, one-refresh retry, migration commit, migration rollback, and unrelated-entry preservation pass automated tests.
- A real WorkBuddy native-OAuth flow completed on macOS and the installed Connector completed canonical `initialize` and `tools/list` directly; the gateway returned 72 namespaced tools.
- Windows and Linux path, command, credential fallback, config shape, and migration behavior are covered by isolated filesystem fixtures; this run did not claim a native Windows or Linux GUI session.
- Direct-OAuth target config generation is covered by fixtures. A separate third-party client UI smoke remains a rollout gate.

## Commands

Default install or upgrade uses the same command and selects the current target capability:

```bash
npx --yes tongzhou-fin-research-expert@latest setup
```

Session diagnostics:

```bash
npx --yes tongzhou-fin-research-expert@latest auth status
npx --yes tongzhou-fin-research-expert@latest auth login
npx --yes tongzhou-fin-research-expert@latest auth logout
```

Migration validates OAuth before replacing old entries:

```bash
npx --yes tongzhou-fin-research-expert@latest migrate-auth --target codex
```

The emitted rollback command restores the backup. It does not revoke the old API Key.
