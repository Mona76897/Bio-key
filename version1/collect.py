import time
import pandas as pd
from pynput import keyboard

# Module 1 & 2: Data Acquisition and Feature Extraction
keystroke_data = []
prev_release_time = None

def on_press(key):
    global prev_release_time
    press_time = time.time()
    # Calculate Flight Time (Latency between keys)
    flight_time = press_time - prev_release_time if prev_release_time else 0
    keystroke_data.append({'key': str(key), 'p_time': press_time, 'flight': flight_time, 'action': 'press'})

def on_release(key):
    global prev_release_time
    release_time = time.time()
    prev_release_time = release_time
    # Calculate Hold Time (Dwell Time)
    for item in reversed(keystroke_data):
        if item['key'] == str(key) and 'dwell' not in item:
            item['dwell'] = release_time - item['p_time']
            break
    if key == keyboard.Key.esc:
        return False

print("BIOKEY ACTIVE: Type naturally for 10-15 minutes. Press ESC to stop.")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# Save processed features to CSV
df = pd.DataFrame(keystroke_data).dropna(subset=['dwell'])
df[['dwell', 'flight']].to_csv('intruder_data.csv', index=False)
print("Success: Dataset saved to 'intuder_data.csv'.")