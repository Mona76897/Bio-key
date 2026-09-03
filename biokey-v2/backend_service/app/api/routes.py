import logging
import time

from fastapi import APIRouter

from app.api.schemas import SecurityPayload, TrustResponse, HealthResponse
from app.core.buffer import buffer_store
from app.core.state_machine import score_session
from app.core.stub_scorer import evaluate_rhythm

logger = logging.getLogger("biokey")

router = APIRouter()

# Set to True once ml_engine/models/*.onnx is wired in via a real scorer.
MODEL_LOADED = False


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", model_loaded=MODEL_LOADED)


@router.post("/api/v1/telemetry/verify", response_model=TrustResponse)
async def verify_telemetry(payload: SecurityPayload):
    buf = buffer_store.get_or_create(payload.session_id)

    # --- LENGTH ALIGNMENT GUARD ---
    # Carried over from V1's fix: dwell/flight can legitimately arrive
    # mismatched in length. Align before storing, don't let it propagate.
    min_len = min(len(payload.keystrokes.dwell_times), len(payload.keystrokes.flight_times))
    dwell = payload.keystrokes.dwell_times[:min_len]
    flight = payload.keystrokes.flight_times[:min_len]

    buf.extend(dwell, flight, payload.mouse.velocities)

    samples = buf.sample_count()
    dwell_window, flight_window, _ = buf.as_lists()

    try:
        raw_score = evaluate_rhythm(dwell_window, flight_window)
    except Exception as e:
        # Log loudly during development — a silently swallowed exception
        # here is exactly what hid the V1 bug for weeks.
        logger.exception(f"[SCORING ERROR] session={payload.session_id}: {e}")
        raw_score = 0.5  # conservative fallback, but now it's LOGGED, not silent

    result = score_session(
        session_id=payload.session_id,
        raw_model_score=raw_score,
        samples_in_window=samples,
    )

    return TrustResponse(
        username=payload.username,
        timestamp=time.strftime("%H:%M:%S"),
        score=result["score"],
        state=result["state"],
        action=result["action"],
        samples_in_window=samples,
    )
