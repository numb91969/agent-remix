# WorkBuddy-native task routing

## Platform capabilities used by Mibao

- natural-language task creation and autonomous planning
- selected workspace and authorized folder access
- file upload, drag-and-drop, pasted screenshots, and referenced context
- continued conversation, interruption, and resumption
- execution progress and intermediate results
- result area: workspace files, browser preview, changes, and artifacts

## Routing rule

Use the platform workspace and authorized-folder capabilities first. Generate an input manifest before processing. Use the built-in execution scripts for deterministic work. Use a multimodal model for observation, orchestration, evidence alignment, and visual QA. Deliver files into the result/artifact area.

## Video boundary

The active model may support video input, but the current WorkBuddy upload surface must be checked for the actual session. If direct video input is unavailable, scan the authorized workspace and build an evidence packet with metadata, thumbnails, sample frames, subtitles, and unknowns.

## Completion rule

Never claim completion without a real output file, a task state, a manifest/log, and verification evidence.
