"""
Per-session rolling FIFO buffer.

Why this exists: V1 cleared its telemetry buffers completely every polling
cycle, which starved the model of context — most requests carried only a
handful of real keystrokes, forcing heavy padding that dominated the score.
This buffer keeps a fixed-size rolling window per session instead, so each
scoring call sees mostly-real recent history rather than a near-empty burst.

One buffer per session_id, so concurrent users/sessions don't bleed into
each other's context.
"""

from collections import deque
from dataclasses import dataclass, field
from threading import Lock


DEFAULT_MAXLEN = 30  # keep in sync with whatever the model expects as input length


@dataclass
class SessionBuffer:
    dwell: deque = field(default_factory=lambda: deque(maxlen=DEFAULT_MAXLEN))
    flight: deque = field(default_factory=lambda: deque(maxlen=DEFAULT_MAXLEN))
    velocity: deque = field(default_factory=lambda: deque(maxlen=DEFAULT_MAXLEN))

    def extend(self, dwell_times, flight_times, velocities):
        self.dwell.extend(dwell_times)
        self.flight.extend(flight_times)
        self.velocity.extend(velocities)

    def sample_count(self) -> int:
        # aligned length is what actually matters for the model input
        return min(len(self.dwell), len(self.flight))

    def as_lists(self):
        n = self.sample_count()
        # take the most recent n from each (they should already be aligned
        # in length most of the time, but guard anyway)
        return list(self.dwell)[-n:], list(self.flight)[-n:], list(self.velocity)


class BufferStore:
    """
    Thread-safe registry of SessionBuffer objects keyed by session_id.
    FastAPI can serve requests concurrently (multiple workers/async tasks),
    so this needs a lock around creation/access — V1's global dict had no
    such protection.
    """

    def __init__(self, maxlen: int = DEFAULT_MAXLEN):
        self._maxlen = maxlen
        self._sessions: dict[str, SessionBuffer] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str) -> SessionBuffer:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionBuffer(
                    dwell=deque(maxlen=self._maxlen),
                    flight=deque(maxlen=self._maxlen),
                    velocity=deque(maxlen=self._maxlen),
                )
            return self._sessions[session_id]


# Module-level singleton — imported by the API layer.
# NOTE: this is in-memory only. Fine for a single-process dev/demo deployment.
# If you later run multiple backend workers/instances, this state won't be
# shared across them — that's a real scalability limitation worth naming
# explicitly in your report rather than discovering it during a demo.
buffer_store = BufferStore()
