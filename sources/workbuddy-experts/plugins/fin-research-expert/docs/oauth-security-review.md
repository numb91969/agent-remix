# OAuth and Connector Security Review

Review date: 2026-07-16

## Boundaries Reviewed

- OAuth access/refresh/device/code values are random, stored only as dedicated HMAC lookups server-side, and never included in telemetry details.
- Public clients use PKCE S256 or RFC 8628 Device Flow. Dynamic registration accepts HTTPS, loopback HTTP, and only the exact WorkBuddy native callback shape `workbuddy://workbuddy/mcp/<connector-id>/oauth/callback`; arbitrary custom schemes and hosts remain rejected.
- Refresh tokens rotate. Reuse compromises only the affected token family; one device revoke does not revoke other devices or old API Keys.
- The WorkBuddy Connector contains only the canonical resource URL; stdio-proxy configs for other clients contain commands and resource URLs, not bearer credentials.
- macOS uses the protected credential backend. Linux fallback files are permission-restricted; Windows uses the platform adapter and ACL-oriented tests.
- Authorization success is committed before optional community handoff. Community configuration, QR, or enterprise-WeChat failures cannot roll back token issuance.
- The standard expert zip excludes Connector source, `.mcp.json`, npm source, `.npm_acc`, `.env*`, test fixtures, and nested release archives.

## Monitoring Review

- Normal Device Flow `authorization_pending` and `slow_down` polling is not counted as authentication failure.
- OAuth failure, refresh, revoke, canonical MCP, migration, and post-auth community events contain allowlisted low-cardinality details only.
- Six-stage OAuth diagnostics expose event counts and, after identity exists, deduplicated users. Pre-login start events explicitly document that user count may be unavailable.
- Research parameter profiles are recorded only after explicit consent and retain names/buckets/digests rather than raw queries or security lists.

## Local Findings

- Source and generated-package scans found no retained live-like OAuth credential in the reviewed paths.
- The first local installer run copied npm source and `.npm_acc` into the local expert tree. The installer exclusion was corrected, the expert was reinstalled, and a second inspection reported no forbidden path.
- The unlocked WorkBuddy UI discovered the local expert, automatically opened the native browser consent page, completed exact-callback PKCE exchange, and loaded 72 protected tools through the renewable session. No token or API Key appeared in the WorkBuddy UI or Connector config. The gateway retains exact redirect matching, one-time authorization codes, PKCE S256, and narrowly scoped custom-scheme validation.
- WorkBuddy 5.2.6 writes the serialized OAuth provider, including access and refresh token values, to its local main-thread log under an `MCP-DEBUG` line after token exchange. The Connector and gateway cannot disable or redact this client-owned log. Treat WorkBuddy diagnostic bundles as credentials until the client redacts these fields; do not upload or share the raw log, and revoke the affected device session before sharing a diagnostic archive.

## Release Blockers

- Do not publish the Connector as an approved WorkBuddy Connector asset until its separate review is complete.
- Obtain a WorkBuddy client fix or written platform acceptance for the `MCP-DEBUG` token logging before broad native-OAuth rollout. This does not block the gateway endpoint or npm Device Flow, whose tests keep tokens out of normal stdout/stderr.
- Keep the npm Device Flow available for clients without native OAuth; do not make the WorkBuddy-only custom callback a cross-client requirement.
- Any raw credential in a package, config, log, screenshot, telemetry export, or support message blocks release and requires credential revocation plus artifact cleanup.
