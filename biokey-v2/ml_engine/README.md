# ml_engine

Owned by: ML Lead.

## Structure

- `data/` — dataset download/prep scripts. **Do not commit raw datasets** —
  `.gitignore` already excludes them. Commit a `download.py` or `README` with
  the source URL instead, so anyone can re-fetch.
- `notebooks/` — EDA, experimentation. Fine to be messy here.
- `models/` — exported `.onnx` artifacts (gitignored — too large / regenerable).
  Log every run in MLflow instead of relying on filenames to track versions.

## Dataset plan

1. **CMU Keystroke Dynamics Benchmark** — fixed-text (subjects retyping the
   same password). Good baseline, but not representative of BioKey's free-text
   continuous monitoring use case. Use for initial model sanity-checking only.
2. **Free-text dataset** (e.g. Buffalo free-text keystroke dataset) — needed
   for evaluation numbers you'll actually defend in the report. Source this
   early (week 1-2), don't discover the mismatch in week 8.
3. **Self-collected adversarial set** — teammates typing into each other's
   enrolled profiles. This is what makes FAR/FRR numbers meaningful (you need
   labeled impostor data, not just genuine-user data). Plan this as a
   scheduled recording session, not an afterthought.

## Deliverables timeline

- **Week 4**: baseline model (Isolation Forest — start here, it's simpler and
  doesn't need much labeled data) trained on CMU, logged in MLflow.
- **Week 6**: exported to ONNX, verified prediction parity against the
  training-time model before handing off to backend_service.
- **Week 8**: real FAR/FRR/latency numbers out of `test_harness/`, using the
  free-text + adversarial datasets.

## Handoff contract to backend_service

Document the exact input shape the exported ONNX model expects (timesteps,
feature order — dwell first or flight first, normalization applied or not)
in a `MODEL_CARD.md` here once you export. The V1 project lost time to a
shape mismatch that silently degraded to a fallback score — don't let that
happen again by leaving the contract undocumented.
