"""
Temporary stand-in for the real ONNX model, so the API contract, buffer,
and state machine can all be built and tested before the ML teammate's
model export is ready. Swap `evaluate_rhythm` for a real ONNX Runtime call
later WITHOUT changing its signature — everything upstream (api/routes.py)
should not need to change when the swap happens.

DELETE THIS FILE once ml_engine/models/*.onnx exists and core/onnx_scorer.py
replaces it. Leaving a stub silently in production is exactly the kind of
thing that caused confusion in V1 — track this as a real TODO, not a
someday-maybe.
"""

import statistics


def evaluate_rhythm(dwell_times: list[float], flight_times: list[float]) -> float:
    """
    Returns a fake-but-plausible 0.0-1.0 'trust' score based on simple
    variance in dwell time, just so the pipeline has *something* dynamic
    to show rather than a hardcoded constant. This has no real biometric
    meaning — do not use these numbers in any report or evaluation.
    """
    if not dwell_times:
        return 0.95

    # low variance (very consistent typing) -> higher fake trust
    # this is NOT a real model, just enough variation to exercise the
    # EMA/state-machine logic end to end during development
    if len(dwell_times) < 2:
        return 0.9

    variance = statistics.pvariance(dwell_times)
    fake_score = max(0.0, min(1.0, 1.0 - variance * 5))
    return fake_score
