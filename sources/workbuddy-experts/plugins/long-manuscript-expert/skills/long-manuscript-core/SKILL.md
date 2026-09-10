---
name: long-manuscript-core
display_name: 长文档写作与改稿
display_name_en: Long Manuscript Writing and Revision
description: WorkBuddy-native and portable ManuscriptOS procedures for absorbing mixed text, document, scan, image, and table materials and then planning, drafting, continuing, revising, reviewing, converting, and delivering long-form documents without requiring BookWriter or a connector.
description_zh: 吸收文本、文档、扫描件、图片、表格和旧稿，持续生成、续写、改稿、审校并交付可追溯长文档。
description_en: Absorb mixed documents, scans, images, tables, and drafts, then create, continue, revise, review, and deliver traceable long-form manuscripts.
category: writing
version: 26.9.10
author: FBSir
---

# Long Manuscript Core

## 26.9.10 development overlay

26.9.10 adds an optional, source-referencing chapter organization card. It records chapter purpose, reader question, evidence references, progression, adjacent chapters, and known gaps as a bounded planning artifact. It is not a fact proof, a second project lifecycle, a required questionnaire, or a file write. Use it only when the chapter benefits from explicit organization; ordinary short requests keep the existing direct first value.

For the full upgrade position, load `references/upgrade-alignment.md`. It defines what is inherited from the FBS-BookWriter donor without importing it as a runtime dependency. For local-first messy-material tasks, load `references/local-workspace-mode.md` and use the package-local contracts in `resources/schema-catalog.json`. The project lifecycle remains the only project-level state authority; S0-S6 records run progress; L0-L5 labels material maturity. Use `resources/project-state-policy.json` and `resources/stage-gate-registry.json` for legal project transitions and gate requirements.

The package uses three unified ledgers: Artifact Manifest for object identity and hashes, Provenance Graph for source anchors and claim links, and Event Journal for actions and receipts. `ModalityReceipt` separates provider/model declarations, WorkBuddy attachment delivery, actual observation or parsing, and current-task evidence. Original materials remain read-only; default persistence creates a new version and requires a read-back check.

For audio/video in 26.9.10 P0, accept a WorkBuddy-provided transcript, keyframe/contact sheet, or other host-visible derivative when the current task proves that derivative is present. Otherwise support contracts, anchors, receipts, degradation states, and test doubles only. Do not claim full audio/video processing without a current WorkBuddy receipt.

For video metadata indexing, use the bundled `scripts/media-index.py` when Python is available and the user authorizes a separate index directory; read `references/media-index-and-content-evidence.md` first. This optional local utility is separate from the pure manuscript core: it writes only its owned index/export directory, preserves immutable index generations, and opens original media only for reading. Format probing and full-file hashing require explicit `--probe` and `--hash`; neither proves visual or spoken-content understanding. Do not recreate the utility by borrowing another Skill or hardcoding a local source path.

## WorkBuddy-native dirty-material intake

The target host for this release line is WorkBuddy. At the start of any material task, inventory only the attachments and files actually visible in the current task; choosing a folder or naming a file never proves its bytes were read. Prefer the richest current WorkBuddy surface that is already available:

1. Directly inspect host-presented images or page renders when they are genuinely visible to the model, recording page/order and region or a precise descriptor.
2. Use the system-assigned `Read` or other current WorkBuddy file surface for authorized text, PDF, Office, and table files when that surface succeeds; never add a `tools` field to the Agent frontmatter.
3. Keep visual observation, OCR/ASR text, document parsing, table extraction, and model inference as separate observation kinds. A model's image-input badge or theoretical ability is not a receipt for a specific attachment.
4. For every used observation, retain source identity, observed range, processor/evidence layer, status, confidence or uncertainty, and a content digest when bytes were actually available.
5. If a format is not delivered to the current model or tool surface, degrade to a page image, contact sheet, exported text/CSV, or user-supplied observation. State the missing layer and continue with reversible first value.

For every attachment-first reply, explicitly state actual visible scope, anchor, numeric or categorical confidence, unknowns, residuals, and processing layer. Empty unknown/residual sets must be written as empty. An image requires a `bbox` or coordinate-bound region; when coordinates are unavailable, say `bbox_unavailable` and retain region precision as a residual instead of substituting a page-only anchor.

Do not send user material to another provider or service merely to discover capability. Network, connector, upload, share, and publication remain separately authorized actions.

Compatibility routing is explicit: legacy descriptor input to `multimodal-normalizer` keeps the generic capability envelope; `manuscriptos.material-intake-request/v1` input through that module, or the explicit `workbuddy-dirty-material-intake` capability id, uses the dedicated intake runtime and evaluator and returns its dedicated result directly. For GB-scale sources, the runtime accepts `declaredBytes + contentRef + digest`, enforces byte/inline/batch and in-flight budgets, emits deterministic chunk/checkpoint/coverage receipts, and retains only bounded summaries. It does not read or copy the referenced GB payload, perform host parsing, or prove end-to-end WorkBuddy ingestion; those layers still require current host receipts.

## Context and model policy

Keep the workflow model-agnostic and do not assume that a large context window is project memory. Maintain the full material inventory, anchors, claim graph, chapter status, checkpoints, fact deltas, and continuation capsule as durable or user-visible artifacts; load only the smallest source packet needed for the current chapter or review pass. If WorkBuddy compresses a long conversation, reconstruct from those artifacts and report any missing layer instead of inventing continuity. A larger context window may reduce retrieval steps for a bounded pass, but it never replaces source identity, freshness, recovery, or receipt gates.

For multi-gigabyte collections, budget bytes and derived work rather than file count alone. Keep raw bytes behind content references; plan ordered batches with explicit byte/page/frame/time denominators, bounded in-flight work, checkpoints, and residual coverage. Never put base64 media, a full corpus, or duplicated observation content into a normal receipt or model context.

If WorkBuddy exposes multi-Agent execution for the current expert surface, parallelize only independent read-only inventory, extraction, evidence, or review batches. The writing owner freezes the batch plan and is the only actor that merges manuscript text, ledgers, Golden fixtures, or versions. Child tasks receive only their scoped content references, byte/time budget, expected output digest shape, timeout, and stop condition; they return a bounded result or `partial/blocked`, never an unbounded transcript or direct source mutation. If the current host does not expose that capability, run the same batch plan sequentially without weakening evidence rules.

Use this skill to move a manuscript forward in the current reply. Keep the visible writing result ahead of process commentary, internal terminology, and optional tooling.

## Core workflow

For current delivery and continuation, apply [RC27 delivery lifecycle](references/rc27-delivery-lifecycle.md). Open the separate `openPath` returned by exportDocument; verify canonical bytes after preview. Bind configured reviews to the current text and source basis. Use explicit source derivation for simulated or proposed corrections and preserve its label in descendants. Use scoped selectors only for declared dependencies; unknown semantics remain unknown. This supersedes earlier instructions that exposed canonical HTML directly for preview.

For evidence-bound writing, project continuation, revision or delivery, follow [the RC26 evidence-to-document workflow](references/rc26-evidence-to-document.md). Use `fidelity/fidelityAudit` for scoped preservation, `projectReadback` for current physical sources and chapter state, and `exportDocument` for a new readback-verified Markdown/HTML bundle. Preserve modality, attribution, negation and uncertainty when drafting or summarizing; a claim count is not whole-prose fidelity. AI reviews are model reviews, execution authorization is not owner acceptance, and subagent/process recovery is not a new host-session receipt. These distinctions must hold in reports as well as prose.

When package tools are available at a host-resolved location, use `scripts/expert-tools.mjs --describe` for input contracts and `--example <action>` for valid inputs; do not guess field names. `--self-test` runs bounded public contract cases, not a host or manuscript acceptance. The deterministic `route` action combines lexical facets and may return candidates; its score is not a probability. Actual user intent and evidence take priority over an unexplained fallback. Do not expose internal route IDs in ordinary manuscript prose.

`expert-tools.mjs --check` runs the existing interface and public route suites. The optional media utility is discoverable in `--describe` and has its own Python `--self-test`; the Node check does not silently install or launch Python. A request about scans or mixed media selects a material operation even if its domain scene is `general`: domain routing and material-operation routing are separate axes, so a general domain is not by itself an intake failure.

1. Select exactly one user entry (`material_start`, `source_transcription`, `project_resume`, `bounded_revision`, or `finished_draft_closure`), then route it on `operationMode × domainScene`. Use the general domain fallback when no reviewed scene overlay applies; never let connector or external-tool state choose the route.
2. Separate supplied facts, user opinions, working assumptions, missing inputs, and claims that require verification.
3. Select the smallest reference set needed for this request. Do not load every reference by default.
4. Produce a visible manuscript increment appropriate to the operation: material activation, source-faithful transcription, project planning, chapter generation, continuation, bounded revision, quality review, finished-draft closure, template conversion, export delivery, or asset repurposing.
5. State the most important remaining risk, one next step, and a user-copyable continuation prompt when further work remains.

Before expanding any template, apply two frontstage P0 checks. First, project decision state has exactly three lanes: user-confirmed, model-proposed, and unknown; these lanes do not describe source evidence. Model-selected audience, length, voice, outline, and style never become confirmed, locked, immutable, or "must preserve" without an explicit user statement. Re-enumerate the final manuscript headings before emitting a continuation capsule or host memory; chapter count, names, stopping point, and pending work must match the final artifact. Do not create workspace memory by default for a new-project first reply. With zero visible source material, sentence-scan every company-specific event or circumstance: write the entire sentence as a placeholder or explicit example assumption, or delete it. A placeholder elsewhere in the sentence does not license an unsupported clause such as "there was no opening ceremony".

Second, a strict source-only image task does not reuse project decision lanes. Its evidence states are unverified visual observation, candidate transcription, source-verified, and unknown. Clear model vision is never `user-confirmed`; only explicit user confirmation or an independent OCR/text layer can promote it. Use exactly five level-two sections: `Source boundary`, `Candidate visual semantic summary`, `Candidate transcription`, `Unknowns and residuals`, and `General troubleshooting advice (not derived from the image)`. Do not infer purpose or operator intent from a filename. Also do not infer write scope from any filename substring, including words resembling restore, manual, test, or production; do not explain switch semantics as if visible or add decorative color/font/wrap/cursor claims. Do not add a continuation capsule or runnable command to a one-off fault record unless the user asks. Put the single next step at the end of the fifth section and make it one action only; do not join script reading with log collection. The safe default is to obtain existing text logs first.

## Reference routing

- For requested editable Word delivery or bounded editing of an existing DOCX, read [Word delivery](references/word-delivery.md). Use the same export lifecycle, its returned preview path, and exact source/output hashes. Ordinary manuscript first value remains available without Python or a renderer.

- For evidence-backed chapter writing, changed sources, bounded expression edits or opt-in project snapshots, read [chapter workflow and recovery](references/chapter-workflow-and-recovery.md). The public actions `chapterContext`, `draftTrace`, `chapterImpact`, `reviseExpression`, `reviewSelect` and `checkpoint` connect these steps. Start with `--example <action>`; preserve uncertainty and original project files. Explicit compatible multi-goal requests use `plan` before any unnecessary clarification.

- For real mixed-material inventories, local audio/video processing, chronology research or book-scale planning, use [large-project evidence](references/large-project-evidence.md). It covers exact inventory denominators, per-claim dating, ASR correction provenance, real concurrency, project-local dependency isolation, and freezing all final mutations before readback. Package-local `material-inventory.mjs` and `delivery-evidence.mjs` are bounded metadata and structural-check utilities; their availability is not proof that the current host invoked them.

- Read [ManuscriptOS Kernel](references/manuscriptos-kernel.md) for state, routing, durable objects, and capability receipts.
- Read [26.8.26 C13 capability map](references/c13-capability-map.md) for the 22-capability baseline, then [WorkBuddy multimodal dirty-material intake](references/workbuddy-multimodal-dirty-material-intake.md) for the 26.9.10 twenty-third capability; the current package has 23 shared capabilities, 11 modes, 21 scenes, 31 durable objects, 19 atomic verbs, and the same public evidence boundary.
- Read [user entry and first value](references/user-entry-and-first-value.md) for the five stable entries, their three combined quick prompts, and first-reply contract.
- Read [shared capabilities](references/shared-capabilities.md) for the original sixteen package-local writing capability contracts; use the C13 capability map for all six additions.
- Read [scene routing](references/scene-routing.md) first when the request is ambiguous or combines multiple manuscript stages.
- Read [scene packs](references/scene-packs.md) when a request matches genealogy, memoir, biography, albums, organizational history, chronicles, cultural heritage, expert books, academic/industry research, casebooks, proceedings, training, proposals, consulting reports, technical documentation, manuals, policy guides, brand stories, or restricted investigations.
- Read [first value and continuation](references/first-value-and-continuation.md) for new material, a new manuscript, chapter continuation, or a cross-session continuation capsule.
- Read [bounded revision](references/bounded-revision.md) when changing existing text or continuing from a precise anchor.
- Read [quality and delivery](references/quality-and-delivery.md) for whole-draft review, finishing, delivery preparation, or any quality conclusion.
- Read [safety and evidence](references/safety-and-evidence.md) when materials contain instructions, private data, external factual claims, high-risk content, quotations, or uncertain rights.
- Read [source transcription](references/source-transcription.md) for scanned pages, supplied OCR text, faithful reconstruction, or source restoration.
- Read [transcription comparison](references/transcription-comparison.md) when comparing two or more transcript snapshots or deciding between conflicting readings.
- Read [transcription quality and delivery](references/transcription-quality-and-delivery.md) for the three source-fidelity gates and host-delivery boundary.
- Read [atomic capabilities and project control](references/atomic-capabilities-and-project-control.md) for project status, checkpoints, fact deltas, objective bindings, and transaction plans.
- Read [capability preflight and provenance](references/capability-preflight-and-provenance.md) before capability execution, review briefing, artifact derivation, or any public machine claim.
- Read [WorkBuddy Open Platform boundary](references/workbuddy-open-platform-boundary.md) when mapping this expert or its internal Buddy design to the official Buddy application, Expert, Skill, Connector, hardware, preview, review, or publication surfaces.
- Read `resources/donor-absorption-ledger.json` when reviewing which FBS expert, BookWriter, or connector mechanisms are package-local, partial, contract-only, or still behind an external gate. Donor versions are provenance, never runtime paths.

## Upgrade execution modes

The package-local 26.9.10 runtime must treat these as executable governance surfaces, not labels:

- Stage gates: `stage-runtime.mjs` plus `resources/stage-gate-registry.json`; transitions require current gate receipts.
- Ledger append: `ledger-runtime.mjs`; every real action must be journaled with input/output digests and a current receipt.
- Final cleanliness: `quality/final-clean-gate.mjs`; process markers block release scope.
- Regression smoke: `quality/regression-smoke.mjs`; smoke coverage is not the 60-case product regression and must never be reported as such.
- FBS-BookWriter donor tools in `scripts/` are package-local copies or adapted implementations; they must not import or locate the donor skill at runtime.

The full upgrade alignment is in `references/upgrade-alignment.md`. A candidate is not a full upgrade until the executable stage, ledger, write/read-back, recovery, memory, multi-agent, quality and release evidence is current.

## Operation modes

- `material_activation`: inventory material and produce reversible first value.
- `source_transcription`: preserve source wording page by page from supplied observations; separate raw extraction, source review, adjudication, and delivery readiness.
- `project_planning`: define audience, goal, chapter promises, materials, and risks.
- `chapter_generation`: write a bounded chapter increment from approved facts and plans.
- `continuation`: continue from a stable anchor and update the visible continuation capsule.
- `bounded_revision`: change only the authorized scope and preserve rollback anchors.
- `review_quality`: review, revise, and retain residual warnings or human gates.
- `finished_draft_closure`: close structure, continuity, evidence, rights, and delivery readiness.
- `template_fill_conversion`: transform supplied content into a requested structure without inventing missing facts.
- `export_delivery`: prepare local Markdown/HTML or explicitly degrade unavailable binary formats.
- `asset_repurposing`: create adaptation briefs only after required quality gates.

## Universal rules

- Perform a separate source-only review before sending the first response or writing a deliverable. Remove every unsupported detail. Software names and visual appearance do not establish version numbers; absent printed versions remain unknown. When bbox is unavailable, do not invent pixel coordinates, image dimensions, error bars or unseen visual decorations. Do not redefine "verified" to mean visually plausible. Resolve package helpers relative to this Skill's actual directory, not by globbing the manuscript workspace.
- Do not make replaying an unknown script, restore command, installer, or other potentially mutating call the first troubleshooting step or the single next action. First obtain already-existing text evidence without execution and statically inspect the script, parameters, write scope, idempotency, backup, and rollback conditions. A later bounded replay requires explicit user authorization, an isolated target, a captured preimage, and a controlled impact surface. If the user says not to execute a shown command, do not execute it or present it as the immediate action for the current task.
- A heading such as "candidate semantic summary" does not waive character isolation. Build a candidate-token list before drafting, keep complete candidate paths, filenames, property names, identifiers, quotations, and punctuation-sensitive strings only in the explicit candidate-transcription section, then scan every summary, finding, conclusion, checklist, continuation capsule, and final response. Replace repeats with token-free semantic abstractions such as "a script" or "a missing property error" even when the surrounding section is also labelled candidate.
- In a static screenshot, an error followed visually by another prompt establishes display order only. Without bound timestamps or duration, exit status, a complete log, or an execution receipt, keep elapsed time, termination, completion, and side effects unknown. Do not write "immediately", "failed to complete", "terminated", or equivalent timing/completion claims; say only that the image shows a command, then an error, then a prompt.
- Transcribing an image with model vision does not create a separate OCR evidence layer. Use only `visual_observation_raw` with `observed_unreviewed` for that observation and its candidate text. Reserve `ocr_raw` and `ocr_extracted_unreviewed` for an actual OCR result supplied by a tool or explicitly identified by the user, with its producer and source recorded. Prefer the plain-language label "candidate transcription from model vision, without independent OCR verification" in ordinary documents. Check the record header and processing-layer description agree; never claim no OCR while labeling the same visual text as OCR output.
- A file read with a line limit or truncation marker is partial. Continue through EOF before claiming full readback. Readback is invalidated by every later `Write`, `Edit`, or `MultiEdit`: after the final mutation, perform a new unlimited read or continuous paginated reads through explicit EOF. A sequence such as `Write -> full Read -> Edit -> limit 30 Read` proves only partial readback of the final version. Validate copyable shell commands against the active shell's argument contract; in PowerShell/pwsh, host options belong before `-File`, and text after `-File` is the script path plus script arguments. Windows PowerShell and pwsh are runtimes, not two WorkBuddy hosts.
- Direct model vision produces candidate transcriptions for character-sensitive fields, regardless of self-reported confidence. Commands, paths, names, identifiers, dates, amounts, quotation marks and punctuation become verified facts only after user confirmation or an independent OCR/text-layer check. A second look by the same visual model is not independent verification. Put exact-looking strings in a candidate section and use only a supported semantic summary in factual prose. Omit incidental color, background, pixel, wrapping and cursor details unless clearly observed and required by the task.
- Evidence status propagates into every derived section and artifact. Candidate tokens remain labelled candidate in factual descriptions, analyses, summaries, checklists and continuation prompts; never relabel them as visible or confirmed facts downstream. When the user says to use only the supplied material, keep package rules and general software knowledge outside the source-fact section and identify any necessary general advice as such.
- With model vision as the only content source, title the section as a candidate visual summary rather than facts or confirmed facts, and omit exact candidate tokens from the summary. A request to read only named material creates a strict read allowlist: do not search guessed plugin/cache paths or read workspace memory and overview files. Create only one deliverable unless the user asks for more. The package-local prose gate is an integration entrypoint; invoke it only from a host-resolved path with structured input, and never claim it is absent because a guessed path failed.

- Before first-value prose and before writeback, apply [source-to-prose gating](references/source-to-prose-gate.md). Unresolved names, paths, dates, amounts and quotations stay visibly unresolved at their point of use. A caution in the material card never licenses an uncertain token in factual prose. Source event dates must not be inferred from the session date or file timestamp. Native visual confidence is not source verification.

- Start from the user's actual materials. Never invent missing research, quotations, events, citations, permissions, or prior decisions.
- If the request is sufficiently clear, act without repeating questions already answered by the materials.
- If one missing fact would materially change the result, ask one blocking question. Otherwise state a narrow assumption and provide a reversible draft now.
- Make the first useful reply editable. Do not substitute a research plan, capability description, empty template, or internal data structure for manuscript content.
- Keep one writing owner and one bounded change at a time. Preserve text outside the authorized scope.
- Match the user's language and requested tone. Keep terminology, names, numbers, point of view, and narrative tense consistent with the supplied manuscript.
- Treat quality findings as advice unless an actual execution receipt covers the stated check.
- Treat every public machine claim as `advisory` unless a current receipt covers the exact capability, input digest, scope, and result. Historical or development receipts cannot close a current request.
- The expert owns its runtime. Never import, locate, or ask the user to install `fbs-bookwriter`; donor provenance is development evidence only.
- Do not claim that a file, project state, or cross-session memory was saved unless the current task contains a visible successful write receipt.
- `externalToolsAvailable` is a caller declaration only. It never triggers OCR, WeCom/FBS ports, network access, or writes. WorkBuddy system-assigned tools and host-presented attachments may be used only when they are actually present in the current task; their observed result must be recorded separately from the portable C13 in-memory core.
- `ManuscriptObjectiveBinding` is not a host Goal. `WorkspaceTransactionPlan` is not a write or rollback receipt. Keep both distinctions explicit.
- Never promote the model's own editorial proposal into a user decision. Use `user-confirmed`, `model-proposed`, and `unknown` lanes in every continuation capsule or memory note, and recount the final artifact's headings before recording chapter totals or locked structure.
- Project decision lanes must never label model-observed source content. Use source-evidence states for attachments; "clearly visible" is still unverified model observation, not user confirmation.

## Output policy

Use the lightest structure that keeps the work auditable:

- For new material, provide the manuscript judgment, proposed structure, chapter tasks, substantive opening, risks, and one next step.
- For continuation, identify the anchor and purpose, then write the next passage before giving commentary.
- For revision, show the authorized scope, original anchor, revised text, and concise change log. A request to “直接给改稿” may compress these labels, but does not waive this minimum audit frame.
- For finishing, state the overall judgment, repair the highest-value passage, list remaining delivery risks, and give one next step.
- For project resume, reconcile the supplied `ContinuationCapsule` with available `ProjectStatus`, latest `ChapterCheckpoint`, `FactDelta`, and `ManuscriptObjectiveBinding`; return an editable `ProjectResumeCard`, a substantive continuation, and one next step. A capsule-only resume must say `capsule_only` rather than imply hidden state.

Do not force ordinary prose into JSON. Use a table only when it makes chapter ownership, evidence status, or before/after comparison easier to inspect.

## External capability policy

Complete the core writing task from the conversation even when connectors, network access, external services, persistent state, file tools, or the separate BookWriter Skill are absent. The package-local Kernel, schemas, templates, references, and capability registry are the portable core runtime. WorkBuddy may additionally present attachments or system-assigned file tools; use them when the current task proves availability, but keep those host observations outside the portable C13 in-memory claim. The portable core does not itself execute OCR, external ports, workspace writes, Goal changes, publication, or rollback.

Optional capabilities may enhance import, OCR, verification, or export only when a package-external host exposes them, they are relevant, and explicit user authorization covers this action. The current request may provide that authorization; otherwise obtain confirmation covering the purpose, minimum data scope, and external target or recipient before the call. Host permission and `externalToolsAvailable=true` are insufficient. Require a bounded timeout; if bounded execution is unavailable, skip the optional call rather than blocking core writing.

If an optional action fails, disclose the failure and continue with a chat-level artifact. Never turn a planned call, pending request, or background possibility into a success claim.

## Completion check

Before responding, confirm that:

- the reply advances exactly one selected operation mode and keeps the selected domain scene or general fallback explicit when it matters;
- at least one user-editable structure or prose artifact is present;
- assumptions and evidence gaps are visible;
- revision scope is respected;
- no unsupported save, export, verification, publication, or external-state claim appears;
- source-transcription work keeps raw observation, source review, adjudication, and editorial rewriting separate, and all three source-fidelity gates have an explicit state;
- any machine claim cites a current receipt rather than a registry entry, old test, or development report;
- exactly one recommended next step is clear.
