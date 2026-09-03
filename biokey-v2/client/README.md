# client

Keystroke capture agent + lockout UI + dashboard. Owned by: Frontend & Scoring
Logic Lead (also owns `backend_service/app/core/` — the scoring engine itself).

## Structure

- `src/` — capture widget (browser JS keydown/keyup listener, or Python
  desktop agent using pynput — pick one and be consistent; V1 used pynput,
  a browser widget is more portable for a live demo).

## Week 1-2 deliverable

A simple typing input that logs key-down/key-up timestamps and computes
dwell time (hold duration) and flight time (gap since last key release).
This doubles as your frontend deliverable — keep it visually simple at
first, polish later.

## Week 3-4 deliverable

Widget POSTs telemetry to `backend_service`'s `/api/v1/telemetry/verify`
endpoint (stub scorer is fine at this point — see backend_service/README.md
for the response contract) and displays the returned score/state live.

## Lessons carried over from V1

- Don't fully clear telemetry buffers every polling cycle — that starves
  the model of real context and forces heavy padding. Trim to a rolling
  window (matching backend's FIFO buffer size) instead.
- Match whatever key names the backend's response contract uses exactly
  (V1 broke silently for weeks over a `score` vs `confidence_score`
  mismatch that a bare `except: pass` hid). Don't swallow response-parsing
  errors silently — log them during development.
