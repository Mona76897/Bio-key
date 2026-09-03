"""
Request/response contract for the telemetry ingestion endpoint.

This is the single source of truth for field names. The V1 prototype lost
weeks to a silent mismatch between 'score' and 'confidence_score' because
the contract only lived in each side's head. Don't repeat that here —
if you need to change a field name, change it here and grep the client
for the old name before you commit.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


# --- INBOUND: what the client agent sends per polling cycle ---

class KeystrokeTelemetry(BaseModel):
    dwell_times: List[float] = Field(
        default_factory=list,
        description="Key hold duration per keystroke, in seconds."
    )
    flight_times: List[float] = Field(
        default_factory=list,
        description="Gap between previous key release and this key press, in seconds."
    )


class MouseTelemetry(BaseModel):
    velocities: List[float] = Field(default_factory=list)


class SecurityPayload(BaseModel):
    username: str
    session_id: str
    keystrokes: KeystrokeTelemetry
    mouse: MouseTelemetry = MouseTelemetry()


# --- OUTBOUND: what the server returns ---

StateLiteral = Literal["WARMUP", "AUTHORIZED", "WARNING", "ISOLATE"]
ActionLiteral = Literal["COLLECTING", "ALLOW_SESSION", "SHADOW_AUDIT", "HARD_LOCKDOWN"]


class TrustResponse(BaseModel):
    username: str
    timestamp: str
    score: float
    state: StateLiteral
    action: ActionLiteral
    samples_in_window: int


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}  # allow the "model_loaded" field name

    status: Literal["ok"]
    model_loaded: bool
    version: str = "v2-stub"
