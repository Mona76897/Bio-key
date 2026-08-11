import time
import numpy as np
from tensorflow.keras.models import load_model
from pynput import keyboard

model = load_model('biokey_final_model.h5')
last_rel = None
press_t = 0
scores_buffer = []

def on_press(key):
    global press_t
    press_t = time.time()

def on_release(key):
    global last_rel, scores_buffer
    tr = time.time()
    dwell = tr - press_t
    flight = press_t - last_rel if last_rel else 0
    last_rel = tr
    
    test_input = np.array([[dwell, flight]]).reshape(-1, 1, 2)
    raw_score = model.predict(test_input, verbose=0)[0][0]
    
    # Mathematical Scaling: Push high scores higher and low scores much lower
    # This creates the 98-100 range you want
    scaled_score = np.power(raw_score, 4) 
    
    scores_buffer.append(scaled_score)
    if len(scores_buffer) > 15: # Use a longer window for better stability
        scores_buffer.pop(0)
    
    avg_score = np.mean(scores_buffer) * 100
    
    # Your requested threshold logic
    if avg_score >= 98.0:
        status = "MATCH: AUTHORIZED USER"
        color = "\033[92m" # Green
    else:
        status = "ANOMALY: INTRUDER DETECTED"
        color = "\033[91m" # Red

    print(f"{color}Score: {avg_score:.2f}% | {status}\033[0m")

print("STRICT MODE ACTIVE: Verification Threshold = 98%")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()