"""
Trust scoring: cold-start honesty threshold, EMA smoothing, multi-tier state machine.

This module intentionally does NOT talk to the ML model directly — it takes
a raw per-window score (0.0-1.0) as input and turns it into a smoothed,
decision-ready state. That separation means the ML teammate can swap the
underlying model without touching this logic, and this logic can be unit
tested without a model loaded at all.
"""

from dataclasses import dataclass, field
from threading import Lock


# --- Tunable thresholds — keep these here, not scattered in the codebase,
# so they can be tuned against real FAR/FRR numbers from test_harness/
# and the change shows up in one place / one diff. ---

MIN_SAMPLES_FOR_SCORING = 15   # below this: WARMUP, don't score at all
EMA_ALPHA = 0.3                # higher = more reactive, lower = smoother
AUTHORIZED_THRESHOLD = 85.0
WARNING_THRESHOLD = 60.0


@dataclass
class SessionTrustState:
    smoothed_score: float = 100.0  # optimistic default until real data arrives
    initialized: bool = False


class TrustStateStore:
    """Thread-safe per-session EMA state, mirroring BufferStore's pattern."""

    def __init__(self):
        self._states: dict[str, SessionTrustState] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> SessionTrustState:
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = SessionTrustState()
            return self._states[session_id]


trust_state_store = TrustStateStore()


def apply_ema(previous_smoothed: float, new_raw_score_pct: float, alpha: float = EMA_ALPHA) -> float:
    """new_raw_score_pct and previous_smoothed are both on a 0-100 scale."""
    return (alpha * new_raw_score_pct) + ((1 - alpha) * previous_smoothed)


def evaluate_state(smoothed_score: float) -> tuple[str, str]:
    """Maps a smoothed 0-100 score to (state, action)."""
    if smoothed_score >= AUTHORIZED_THRESHOLD:
        return "AUTHORIZED", "ALLOW_SESSION"
    elif smoothed_score >= WARNING_THRESHOLD:
        return "WARNING", "SHADOW_AUDIT"
    else:
        return "ISOLATE", "HARD_LOCKDOWN"


def score_session(session_id: str, raw_model_score: float, samples_in_window: int) -> dict:
    """
    Main entry point called by the API layer.

    raw_model_score: 0.0-1.0 output from the ML model for this window
                      (ignored if samples_in_window < MIN_SAMPLES_FOR_SCORING)
    samples_in_window: aligned dwell/flight sample count currently in the buffer

    Returns a dict with keys: score, state, action — ready to drop into
    the TrustResponse schema.
    """
    state_obj = trust_state_store.get_or_create(session_id)

    # --- COLD-START HONESTY THRESHOLD ---
    # Don't pad a near-empty window and report a fake-confident number.
    # This was the root cause of the score-clustering artifact in V1.
    if samples_in_window < MIN_SAMPLES_FOR_SCORING:
        return {
            "score": round(state_obj.smoothed_score, 1),
            "state": "WARMUP",
            "action": "COLLECTING",
        }

    raw_pct = raw_model_score * 100.0
    new_smoothed = apply_ema(state_obj.smoothed_score, raw_pct)
    state_obj.smoothed_score = new_smoothed
    state_obj.initialized = True

    state, action = evaluate_state(new_smoothed)
    return {
        "score": round(new_smoothed, 1),
        "state": state,
        "action": action,
    }
