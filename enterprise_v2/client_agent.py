import time
import requests
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard, mouse
import threading

# --- CONFIGURATION ---
SERVER_URL = "http://127.0.0.1:8000/api/v1/telemetry/verify"
USERNAME = "mona_secure_01"
SESSION_ID = "session_live_99"
UNLOCK_PIN = "1234"

# --- SMART BRAKES ---
is_locked = False
cooldown_until = 0.0  # Timestamp until which lockdown is completely muted

# --- TELEMETRY BUFFERS ---
dwell_buffer = []
flight_buffer = []
velocity_buffer = []

last_release_time = time.time()
key_press_times = {}

# --- LOCKDOWN WINDOW FUNCTION WITH 1-MINUTE SMART COOLDOWN ---
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
    
    lbl = tk.Label(root, text="⚠️ ZERO-TRUST LOCKDOWN ACTIVATED", font=("Helvetica", 28, "bold"), fg="#ff3333", bg="#1a1a1a")
    lbl.pack(pady=50)
    
    lbl2 = tk.Label(root, text="Biometric anomaly detected. Input authorization PIN to unlock.", font=("Helvetica", 14), fg="#ffffff", bg="#1a1a1a")
    lbl2.pack(pady=10)
    
    pin_entry = tk.Entry(root, font=("Helvetica", 18), show="*", justify="center")
    pin_entry.pack(pady=20)
    pin_entry.focus_set()
    
    def check_pin():
        global is_locked, cooldown_until
        if pin_entry.get() == UNLOCK_PIN:
            is_locked = False
            # 💡 Give the user 60 seconds of complete immunity to work comfortably!
            cooldown_until = time.time() + 60.0 
            print("\n[🛡️ COOLDOWN ACTIVATED] Lock muted for 60 seconds to allow rhythm stabilization.")
            root.destroy()
        else:
            messagebox.showerror("Access Denied", "Incorrect Security Credentials!")
            pin_entry.delete(0, tk.END)
            
    btn = tk.Button(root, text="VERIFY IDENTITY", command=check_pin, font=("Helvetica", 12, "bold"), bg="#ff3333", fg="white", padx=20, pady=5)
    btn.pack(pady=10)
    root.mainloop()

# --- INPUT TRACKING LOGIC ---
def on_press(key):
    if is_locked: return
    try:
        if key not in key_press_times: key_press_times[key] = time.time()
    except Exception: pass

def on_release(key):
    if is_locked: return
    global last_release_time
    try:
        if key in key_press_times:
            press_time = key_press_times.pop(key)
            now = time.time()
            dwell_buffer.append(float(now - press_time))
            flight_buffer.append(float(press_time - last_release_time))
            last_release_time = now
    except Exception: pass

def on_move(x, y):
    if is_locked: return
    global last_mouse_time, last_x, last_y
    now = time.time()
    dt = now - last_mouse_time
    if dt > 0:
        distance = ((x - last_x)**2 + (y - last_y)**2)**0.5
        velocity = distance / dt
        if velocity > 5.0: velocity_buffer.append(float(velocity))
    last_x, last_y = x, y
    last_mouse_time = now

last_mouse_time = time.time()
last_x, last_y = 0, 0

k_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
m_listener = mouse.Listener(on_move=on_move)
k_listener.start()
m_listener.start()

print("[AGENT RUNNING] Telemetry streaming actively protected by smart cooldown brakes.")

# --- AGENT TRANSMISSION LOOP ---
try:
    while True:
        time.sleep(3.0)
        if is_locked: continue
            
        has_real_mouse_activity = any(v > 5.0 for v in velocity_buffer) if velocity_buffer else False
        has_keyboard_activity = len(dwell_buffer) > 0
        
        if not has_keyboard_activity and not has_real_mouse_activity:
            dwell_buffer.clear()
            flight_buffer.clear()
            velocity_buffer.clear()
            continue
            
        payload_dwells = list(dwell_buffer)
        payload_flights = list(flight_buffer)
        payload_velocities = list(velocity_buffer) if velocity_buffer else [50.0]
        
        # --- NEW ROLLING HISTORY SLIDING WINDOW ---
        MAX_BUFFER_LEN = 30  # Keeps the last 30 events in memory
        
        payload_dwells = list(dwell_buffer)
        payload_flights = list(flight_buffer)
        payload_velocities = list(velocity_buffer) if velocity_buffer else [50.0]
        
        # 🔄 Instead of clearing everything, trim the buffers to keep recent history!
        if len(dwell_buffer) > MAX_BUFFER_LEN:
            del dwell_buffer[:-MAX_BUFFER_LEN]
        if len(flight_buffer) > MAX_BUFFER_LEN:
            del flight_buffer[:-MAX_BUFFER_LEN]
        if len(velocity_buffer) > MAX_BUFFER_LEN:
            del velocity_buffer[:-MAX_BUFFER_LEN]
        
        structured_payload = {
            "username": USERNAME,
            "session_id": SESSION_ID,
            "keystrokes": {"dwell_times": payload_dwells, "flight_times": payload_flights},
            "mouse": {"velocities": payload_velocities}
        }
        
        try:
            response = requests.post(SERVER_URL, json=structured_payload)
            if response.status_code == 200:
                data = response.json()
                
                # Show active status indicator in console
                cooldown_left = max(0, int(cooldown_until - time.time()))
                status_msg = f"| Muted ({cooldown_left}s)" if cooldown_left > 0 else ""
                print(f"[STREAM SUCCESS] Score: {data['confidence_score']}% | Verdict: {data['verdict']} {status_msg}")
                
                # Check thresholds before locking down
                if data['verdict'] == "ISOLATE" and len(payload_dwells) >= 3 and time.time() > cooldown_until:
                    threading.Thread(target=trigger_lockdown_gui, daemon=True).start()
        except Exception:
            pass

except KeyboardInterrupt:
    print("\n[AGENT STOPPED]")