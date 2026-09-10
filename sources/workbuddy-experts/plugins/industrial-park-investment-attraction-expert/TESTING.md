# 26.9.6 package verification

Run from this package root with Node.js 22 or newer:

```text
npm run verify
npm test
npm run package -- --output ../../dist/candidate/industrial-park-investment-attraction-expert-26.9.6-review-20260905-r6.zip
```

The verifier checks the candidate manifest, five skills, JSON contracts and schemas, the legacy `26.7.27` schema snapshot, the compatibility section, and the absence of bundled MCP/connector configuration. Tests use only synthetic fixtures and never read WorkBuddy sessions, credentials, user files or the installed package.

Passing these commands proves package structure and deterministic compatibility behavior only. It does not prove WorkBuddy loaded the candidate, that a marketplace listing was updated, or that a real user asset migrated.
