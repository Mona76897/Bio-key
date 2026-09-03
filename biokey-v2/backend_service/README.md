# backend_service

FastAPI ingestion + inference + scoring engine. Owned by: Lead Architect.

## Structure

- `app/api/` — HTTP endpoints only (ingestion, health check). Thin — no scoring
  logic lives here, it just validates input and calls into `app/core/`.
- `app/core/` — the actual engineering contribution:
  - Rolling FIFO buffer (fixed-size, per-session)
  - Cold-start honesty threshold (return `WARMUP` state instead of scoring on
    insufficient/padded data)
  - EMA smoothing
  - Multi-tier state machine (AUTHORIZED / WARNING / ISOLATE)

## Week 3-4 milestone (must work before anything else builds on top)

`POST /api/v1/telemetry/verify` accepts a payload, runs it through a **stub**
scorer (fixed/random score is fine at this stage), returns a response shaped
exactly like the real one will be. Getting the *shape* of the response contract
right now means the ML teammate's real model and the frontend's dashboard can
both build against it without waiting on each other.

### Response contract (lock this early — both teammates build against it)

```json
{
  "username": "string",
  "timestamp": "HH:MM:SS",
  "score": 87.9,
  "state": "AUTHORIZED | WARNING | ISOLATE | WARMUP",
  "action": "ALLOW_SESSION | SHADOW_AUDIT | HARD_LOCKDOWN | COLLECTING",
  "samples_in_window": 12
}
```

(Single `score` key only this time — no `confidence_score` alias. Fix the
client to match the server, not the other way around, this time.)

## Known lessons carried over from V1 (don't repeat these)

- Don't let a bare `except: pass` swallow errors silently — log them.
- `dwell_times` and `flight_times` can arrive mismatched in length — always
  guard before `np.column_stack`.
- Padding a mostly-empty window produces a fake-confident score — return
  `WARMUP` instead (see cold-start threshold above), don't pad-and-pretend.
