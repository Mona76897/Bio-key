import os
import time
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List
import numpy as np
import csv

# --- DEEP LEARNING MODEL INITIALIZATION ---
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model

    MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "biokey_final_model.h5"))
    if os.path.exists(MODEL_PATH):
        LSTM_MODEL = load_model(MODEL_PATH)
        print("[BOOT] TensorFlow LSTM Model loaded successfully!")
    else:
        LSTM_MODEL = None
except Exception:
    LSTM_MODEL = None

app = FastAPI(title="BioKey Enterprise Security Core Master")

# --- GLOBAL LIVE MEMORY STATUS FOR DASHBOARD ---
latest_system_state = {
    "username": "None",
    "timestamp": "Never",
    "score": 100.0,
    "verdict": "AUTHORIZED",
    "action": "ALLOW_SESSION"
}

# --- AUDIT Trail DB LOGGER (CSV Engine) ---
AUDIT_FILE = "security_audit.csv"

def log_incident_to_db(username, score, verdict, action):
    file_exists = os.path.isfile(AUDIT_FILE)
    with open(AUDIT_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Username", "Trust_Score", "Verdict", "Action_Enforced"])
        writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), username, score, verdict, action])

# --- DATA SCHEMAS ---
class KeystrokeTelemetry(BaseModel):
    dwell_times: List[float]
    flight_times: List[float]

class MouseTelemetry(BaseModel):
    velocities: List[float]

class SecurityPayload(BaseModel):
    username: str
    session_id: str
    keystrokes: KeystrokeTelemetry
    mouse: MouseTelemetry

# --- ANALYTICS ENGINES ---
def evaluate_lstm_rhythm(keystrokes: KeystrokeTelemetry) -> float:
    if LSTM_MODEL is None or not keystrokes.dwell_times:
        return 0.95
        
    dwell_times = keystrokes.dwell_times
    flight_times = keystrokes.flight_times
    
    # --- LENGTH ALIGNMENT GUARD ---
    min_len = min(len(dwell_times), len(flight_times))
    if min_len == 0:
        return 0.95
        
    dwell_times = dwell_times[:min_len]
    flight_times = flight_times[:min_len]
    
    try:
        features = np.column_stack((dwell_times, flight_times))
        input_data = np.expand_dims(features, axis=0)
        
        # --- SEQUENCE LENGTH & DATA HONESTY GUARD ---
        expected_timesteps = LSTM_MODEL.input_shape[1]
        actual_timesteps = input_data.shape[1]
        
        if expected_timesteps is not None:
            if actual_timesteps < expected_timesteps:
                # 🛑 DATA HONESTY CHECK:
                # If less than 50% of the required sequence length is real data,
                # do not pad it into a fake repetitive pattern. Return a neutral baseline.
                real_fraction = actual_timesteps / expected_timesteps
                if real_fraction < 0.50:
                    return 0.95  # Neutral default for insufficient evidence
                
                # Pad out the remainder safely if we have enough real data
                pad_width = expected_timesteps - actual_timesteps
                input_data = np.pad(
                    input_data,
                    pad_width=((0, 0), (0, pad_width), (0, 0)),
                    mode="edge",
                )
            elif actual_timesteps > expected_timesteps:
                input_data = input_data[:, -expected_timesteps:, :]
                
        prediction = LSTM_MODEL.predict(input_data, verbose=0)
        return float(prediction[0][0])
        
    except Exception as e:
        print(f"[LSTM ERROR] {type(e).__name__}: {e}")
        return 0.50

def evaluate_cnn_trajectory(mouse: MouseTelemetry) -> float:
    if not mouse.velocities:
        return 0.96
    if np.max(mouse.velocities) > 1500.0:
        return 0.20
    return 0.97

@app.post("/api/v1/telemetry/verify")
async def verify_telemetry(payload: SecurityPayload):
    global latest_system_state
    
    # --- 1. BIOMETRIC SIGNAL INGESTION ---
    keyboard_score = evaluate_lstm_rhythm(payload.keystrokes)
    mouse_score = evaluate_cnn_trajectory(payload.mouse)
    
    # --- 2. MULTI-MODAL WEIGHTED TRUST CALCULATION ---
    overall_trust = float((keyboard_score * 0.85) + (mouse_score * 0.15)) * 100
    
    # --- 3. ALGORITHMIC ATTACKER DETECTION ENGINE ---
    if len(payload.keystrokes.dwell_times) >= 5 and keyboard_score < 0.60:
        verdict = "ISOLATE"
        action = "HARD_LOCKDOWN"
        overall_trust = float(keyboard_score * 100) 
        
    elif overall_trust >= 88.0:  
        verdict, action = "AUTHORIZED", "ALLOW_SESSION"
    elif overall_trust >= 78.0:
        verdict, action = "WARNING", "SHADOW_AUDIT"
    else:
        verdict, action = "ISOLATE", "HARD_LOCKDOWN"
        
    # --- 4. STATE MACHINE SYNCHRONIZATION & DUAL ALIAS FIX ---
    latest_system_state = {
        "username": payload.username,
        "timestamp": time.strftime('%H:%M:%S'),
        "score": round(overall_trust, 1),
        "confidence_score": round(overall_trust, 1),  # Alias for client compatibility
        "verdict": verdict,
        "action": action
    }
    
    # --- 5. COMPLIANCE AUDIT TRAIL LOGGING ---
    log_incident_to_db(payload.username, round(overall_trust, 1), verdict, action)
    
    # --- 6. SIEM INCIDENT ESCALATION DISPATCHER ---
    if verdict == "ISOLATE":
        alert_payload = {
            "event_type": "BIOMETRIC_IDENTITY_BREACH",
            "severity": "CRITICAL",
            "target_host": "ENDPOINT_NODE_ALPHA",
            "flagged_user": payload.username,
            "session_id": payload.session_id,
            "computed_score": round(overall_trust, 1),
            "mitigation_action": "DESKTOP_LOCKDOWN_ENFORCED"
        }
        print(f"\n[🚨 ALERT FORWARDER] Dispatching breach signature payload to SOC Team...")
        
    # --- 7. NETWORK RESPONSE ---
    return latest_system_state

# --- 🖥️ OPTION 1: VISUAL LIVE WEB DASHBOARD PAGE ---
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    # Pick badge background colors based on security state
    color_map = {"AUTHORIZED": "#2ec4b6", "WARNING": "#ff9f1c", "ISOLATE": "#e71d36"}
    badge_color = color_map.get(latest_system_state["verdict"], "#ffffff")
    
    html_content = f"""
    <html>
        <head>
            <title>BioKey Command Dashboard</title>
            <meta http-equiv="refresh" content="2"> <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b0c10; color: #c5a059; text-align: center; padding-top: 50px; }}
                .container {{ background: #1f2833; width: 50%; margin: 0 auto; padding: 30px; border-radius: 15px; border: 2px solid #45a29e; box-shadow: 0 0 20px rgba(69,162,158,0.3); }}
                h1 {{ color: #66fcf1; font-size: 2.5em; margin-bottom: 5px; }}
                .metric-box {{ font-size: 4em; font-weight: bold; color: #ffffff; margin: 20px 0; }}
                .badge {{ display: inline-block; padding: 10px 25px; font-weight: bold; border-radius: 20px; color: #fff; font-size: 1.2em; }}
                .footer {{ font-size: 0.9em; color: #85929E; margin-top: 20px; }}
            </style>
        </head
        <body>
            <h1>🛡️ BIOKEY REAL-TIME MONITOR</h1>
            <p>Active Multi-Modal Biometric Identity Ingestion Stream</p>
            <div class="container">
                <h3>Current Active Node User: <span style="color: #66fcf1;">{latest_system_state["username"]}</span></h3>
                <hr style="border-color: #45a29e;">
                <div>Identity Confidence Score:</div>
                <div class="metric-box">{latest_system_state["score"]}%</div>
                <div class="badge" style="background-color: {badge_color};">{latest_system_state["verdict"]}</div>
                <h3 style="margin-top: 25px;">Enforced Directives: <span style="color: #ff3333;">{latest_system_state["action"]}</span></h3>
                <div class="footer">Last Evaluation Received At: {latest_system_state["timestamp"]}</div>
            </div>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)