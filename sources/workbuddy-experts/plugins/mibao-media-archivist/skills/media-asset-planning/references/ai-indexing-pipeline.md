# AI indexing pipeline

Use a cost-aware order:

1. inspect technical metadata
2. make thumbnails and keyframes
3. OCR images and keyframes
4. transcribe audio with timestamps
5. create lightweight tags and embeddings
6. enrich selected segments with expensive vision models
7. send low-confidence results to human review

Every result must point back to an asset and a page, frame, or timecode.
