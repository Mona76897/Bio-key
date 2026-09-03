"""
BioKey V2 client agent — captures keystroke timing and streams it to the
backend_service ingestion endpoint.

Changes from the V1 (legacy/v1_demo) version:
  - Points at the new /api/v1/telemetry/verify contract: reads 'state' and
    'score' (no more 'confidence_score' alias — the server only sends 'score'
    now, so this client matches it exactly).
  - Buffers are TRIMMED to a rolling window each cycle instead of fully
    cleared, so the server's FIFO buffer gets real overlapping context
    instead of tiny near-empty bursts (this was the root cause of the
    score-clustering artifact we diagnosed in V1).
  - Lockdown now triggers on state == "ISOLATE" (was verdict == "ISOLATE").
  - Response-parsing errors are now logged, not silently swallowed —
    a silent 'except: pass' around a bad key name is what hid the V1
    KeyError bug for weeks.
"""

import time
import uuid
import logging
import threading

import requests
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard, mouse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("biokey-client")

# --- CONFIGURATION ---
SERVER_URL = "http://127.0.0.1:8000/api/v1/telemetry/verify"
USERNAME = "mona_secure_01"
SESSION_ID = f"session_{uuid.uuid4().hex[:8]}"  # unique per run, avoids stale server-side state
UNLOCK_PIN = "1234"
POLL_INTERVAL_SECONDS = 3.0

# Must match backend_service's core/buffer.py DEFAULT_MAXLEN so the client
# doesn't discard data the server would otherwise have kept.
ROLLING_WINDOW_MAXLEN = 30

# --- SMART BRAKES ---
is_locked = False
cooldown_until = 0.0  # timestamp until which lockdown is muted

# --- TELEMETRY BUFFERS (rolling, not cleared each cycle) ---
dwell_buffer = []
flight_buffer = []
velocity_buffer = []

last_release_time = time.time()
key_press_times = {}

# Tracks buffer length at the last transmission, so we can tell whether
# NEW samples arrived since then — independent of the rolling trim.
# Without this, a persistent (non-cleared) buffer looks "active" forever
# after the first keystroke, even once the user has stopped typing.
last_sent_dwell_count = 0
last_sent_velocity_count = 0


# --- LOCKDOWN WINDOW ---
def trigger_lockdown_gui():
    global is_locked, cooldown_until
    if is_locked or time.time() < cooldown_until:
        return

    is_locked = True

    root = tk.Tk()
    root.title("BioKey Terminal Lock")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a1a")

    root.protocol("WM_DELETE_WINDOW", lambda: None)

    lbl = tk.Label(root, text="⚠️ SESSION ISOLATED", font=("Helvetica", 28, "bold"), fg="#ff3333", bg="#1a1a1a")
    lbl.pack(pady=50)

    lbl2 = tk.Label(root, text="Biometric anomaly detected. Enter PIN to unlock.", font=("Helvetica", 14), fg="#ffffff", bg="#1a1a1a")
    lbl2.pack(pady=10)

    pin_entry = tk.Entry(root, font=("Helvetica", 18), show="*", justify="center")
    pin_entry.pack(pady=20)
    pin_entry.focus_set()

    def check_pin():
        global is_locked, cooldown_until
        if pin_entry.get() == UNLOCK_PIN:
            is_locked = False
            cooldown_until = time.time() + 60.0
            logger.info("[COOLDOWN] Lock muted for 60s to allow rhythm stabilization.")
            root.destroy()
        else:
            messagebox.showerror("Access Denied", "Incorrect PIN.")
            pin_entry.delete(0, tk.END)

    btn = tk.Button(root, text="VERIFY IDENTITY", command=check_pin,
                     font=("Helvetica", 12, "bold"), bg="#ff3333", fg="white", padx=20, pady=5)
    btn.pack(pady=10)
    root.mainloop()


# --- INPUT TRACKING ---
def on_press(key):
    if is_locked:
        return
    try:
        if key not in key_press_times:
            key_press_times[key] = time.time()
    except Exception as e:
        logger.debug(f"on_press error: {e}")


def on_release(key):
    if is_locked:
        return
    global last_release_time
    try:
        if key in key_press_times:
            press_time = key_press_times.pop(key)
            now = time.time()
            dwell_buffer.append(float(now - press_time))
            flight_buffer.append(float(press_time - last_release_time))
            last_release_time = now
    except Exception as e:
        logger.debug(f"on_release error: {e}")


def on_move(x, y):
    if is_locked:
        return
    global last_mouse_time, last_x, last_y
    now = time.time()
    dt = now - last_mouse_time
    if dt > 0:
        distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
        velocity = distance / dt
        if velocity > 5.0:
            velocity_buffer.append(float(velocity))
    last_x, last_y = x, y
    last_mouse_time = now


last_mouse_time = time.time()
last_x, last_y = 0, 0

k_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
m_listener = mouse.Listener(on_move=on_move)
k_listener.start()
m_listener.start()

logger.info(f"[AGENT RUNNING] session_id={SESSION_ID} — streaming to {SERVER_URL}")


def trim_rolling(buf: list, maxlen: int):
    """Keep only the most recent `maxlen` entries — mutates in place."""
    if len(buf) > maxlen:
        del buf[:-maxlen]


# --- TRANSMISSION LOOP ---
try:
    while True:
        time.sleep(POLL_INTERVAL_SECONDS)
        if is_locked:
            continue

        # Compare current buffer length against what we had at the last
        # transmission — this is "did anything NEW happen," not "is the
        # buffer non-empty" (which would be permanently true once any
        # typing has ever occurred, since we no longer fully clear it).
        new_keyboard_events = len(dwell_buffer) - last_sent_dwell_count
        new_mouse_events = len(velocity_buffer) - last_sent_velocity_count

        if new_keyboard_events <= 0 and new_mouse_events <= 0:
            continue  # genuinely idle — don't re-send stale data

        payload_dwells = list(dwell_buffer)
        payload_flights = list(flight_buffer)
        payload_velocities = list(velocity_buffer) if velocity_buffer else []

        # Rolling trim — NOT a full clear. This is the key V1 -> V2 fix:
        # the server's FIFO buffer needs real overlapping context, not a
        # tiny fresh burst every 3 seconds.
        trim_rolling(dwell_buffer, ROLLING_WINDOW_MAXLEN)
        trim_rolling(flight_buffer, ROLLING_WINDOW_MAXLEN)
        trim_rolling(velocity_buffer, ROLLING_WINDOW_MAXLEN)

        # Record what we just sent so the NEXT cycle can tell whether
        # anything new arrived (post-trim lengths, since that's what
        # will still be there next time we check).
        last_sent_dwell_count = len(dwell_buffer)
        last_sent_velocity_count = len(velocity_buffer)

        structured_payload = {
            "username": USERNAME,
            "session_id": SESSION_ID,
            "keystrokes": {"dwell_times": payload_dwells, "flight_times": payload_flights},
            "mouse": {"velocities": payload_velocities},
        }

        try:
            response = requests.post(SERVER_URL, json=structured_payload, timeout=5)
            response.raise_for_status()
            data = response.json()

            cooldown_left = max(0, int(cooldown_until - time.time()))
            status_msg = f"| Muted ({cooldown_left}s)" if cooldown_left > 0 else ""

            logger.info(
                f"Score: {data['score']}% | State: {data['state']} "
                f"| Samples: {data['samples_in_window']} {status_msg}"
            )

            if data["state"] == "ISOLATE" and time.time() > cooldown_until:
                threading.Thread(target=trigger_lockdown_gui, daemon=True).start()

        except requests.exceptions.RequestException as e:
            logger.warning(f"[NETWORK ERROR] Could not reach server: {e}")
        except KeyError as e:
            logger.error(f"[RESPONSE SHAPE ERROR] Missing expected field {e} in server response: {data}")
        except Exception as e:
            logger.error(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}")

except KeyboardInterrupt:
    logger.info("[AGENT STOPPED]")
