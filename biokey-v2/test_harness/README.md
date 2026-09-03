# test_harness

The evaluation methodology — this produces the FAR/FRR/latency numbers that
go in your report and defend your abstract's claims. Shared ownership
(Lead Architect sets it up, ML Lead feeds it labeled data).

## What it needs to do

1. Replay labeled sessions (genuine user + adversarial/impostor) through the
   scoring pipeline exactly as if they arrived live.
2. Compute:
   - **FAR** (False Acceptance Rate) — impostor sessions incorrectly scored
     AUTHORIZED.
   - **FRR** (False Rejection Rate) — genuine sessions incorrectly scored
     ISOLATE.
   - **Detection latency** — wall-clock time from "impostor starts typing"
     to the system emitting ISOLATE (not just raw inference time — this
     should include the EMA smoothing and sustained-window delay, since
     that's the real security/usability tradeoff being measured).
3. Output a simple report (CSV or markdown table) — this is what goes
   directly into your project report and viva slides.

## Priority

Build this as soon as backend_service's core scoring loop exists (even
with a stub or early model) — don't wait until week 9. It's also your
regression test: any time thresholds or the model get tuned, rerun this
to confirm you didn't quietly make FAR/FRR worse.
