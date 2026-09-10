# OAuth Local Validation

Validation date: 2026-07-16 (Asia/Shanghai)

This record covers the unpublished single-Connector expert and an isolated local gateway. It contains no raw access token, refresh token, API Key, user code, phone, portal cookie, or QR payload.

## Test Shape

- WorkBuddy: 5.2.6 on macOS.
- Expert: `fin-research-expert` 0.12.1 installed under the local `my-experts` marketplace.
- Connector: `tongzhou-fin-research` installed under the local Connector marketplace and registered in its local catalog.
- Gateway/console: production OAuth resource at `https://mcp-gateway.textmind-gz.com` plus isolated local contract tests.
- Upstreams: the four production service families aggregated behind the canonical MCP resource.

## Results

| Check | Result | Evidence boundary |
|---|---|---|
| WorkBuddy native OAuth and PKCE | Pass | WorkBuddy dynamically registered its public client, opened the browser consent page, used the same verified custom callback for authorization and token exchange, and stored a renewable session without exposing tokens in UI or Connector config. |
| Canonical MCP initialize | Pass | Installed Connector established the production Streamable HTTP resource after OAuth. |
| Canonical tools/list | Pass | The protected production request returned 72 namespaced tools across the four service families. |
| Community handoff independence | Pass (automated) | Console v0.18.2 renders authorization completion before invoking the native callback and loads the optional community entry independently; 18 responsive Playwright cases pass. |
| Real upstream boundary | Pass with expected degradation | Configured internal upstream addresses were unreachable from this local network and returned 503. Repeating with mock upstream succeeded, confirming an upstream availability issue rather than an OAuth/Connector failure. |
| Expert/Connector local installation | Pass | Installer copied the expert and Connector, updated only the local Connector catalog, and left the source Connector unchanged. |
| Installed package secret boundary | Pass | Installed expert contained neither `.npm_acc` nor npm source, `.env*`, raw credentials, or embedded Connector source. |
| WorkBuddy process restart and marketplace discovery | Pass for prior proxy build | WorkBuddy 5.2.6 restarted and rediscovered the local Connector; native-OAuth restart reuse remains in the final manual matrix. |
| WorkBuddy first connection prompt | Pass | The unlocked WorkBuddy UI discovered expert 0.12.1 and displayed one `同舟金融研究` connection prompt; no legacy four-Key form appeared. |
| WorkBuddy Connector enable and original request | Pass | After explicit browser confirmation, WorkBuddy enabled the single Connector and completed protected `initialize` and `tools/list` without a legacy API Key. |
| WorkBuddy new conversation | Pass for prior proxy build | A second expert task reused the previous renewable session; native-OAuth new-conversation reuse remains in the final manual matrix. |
| WorkBuddy restart call | Pass for prior proxy build | A graceful WorkBuddy quit/relaunch reused the previous renewable session; native-OAuth restart reuse remains in the final manual matrix. |
| WorkBuddy first native authorization | Pass | After clearing the disposable legacy credential and reconnecting, WorkBuddy automatically opened the PC browser consent page; the exact custom callback succeeded and the Connector loaded 72 tools. |
| WorkBuddy client log redaction | Fail / external | WorkBuddy 5.2.6 logged its serialized OAuth provider, including bearer credentials, in a local `MCP-DEBUG` line. Gateway and Connector configs remain credential-free, but broad rollout requires a WorkBuddy-side redaction fix or explicit platform acceptance. |

## Automated Regression

- Gateway suite: 115 tests passed.
- Expert structure/installer suite: 36 tests passed.
- npm auth/proxy/migration/target suite: 35 tests passed.
- Portal OAuth/community Playwright: 18 project cases passed across 1440x900, 1920x1080, and 390x844.

The Playwright screenshots validate browser consent, connected-first community handoff, and responsive layout. The real WorkBuddy log separately verifies native callback and protected MCP completion.

## Remaining Manual Matrix

The native first-authorization and protected MCP handshake are complete. Remaining rollout checks are:

1. Open a new expert conversation and restart WorkBuddy once with the native session, confirming neither path reauthorizes.
2. Deny one disposable native browser authorization and confirm the Connector remains disconnected with no research fallback.
3. Let one native authorization request expire and confirm a fresh `连接` action creates a new request.
4. Revoke only this device in the Portal and confirm the next call requests reauthorization while other sessions remain valid.

Redact the QR, user code, account identifiers, request IDs, and local paths before retaining screenshots.
