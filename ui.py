import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog as sd
import time
import numpy as np
import sqlite3
import hashlib
import smtplib
import threading
from email.message import EmailMessage
from tensorflow.keras.models import load_model
from pynput import keyboard, mouse
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- SYSTEM CONFIGURATION ---
SMTP_USER = "mohanapriyap23cs@psnacet.edu.in"
SMTP_PASS = "shga pomz khss qagx" 
ALERT_RECEIVER = "mp6264072@gmail.com"

class BioKeyEnterpriseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BioKey Multimodal Zero-Trust Security Suite")
        self.geometry("1150x800")
        self.configure(bg="#0a0a0a")
        
        # Core Security variables
        self.active_user = None
        self.is_locked = False
        self.alert_sent = False
        self.emergency_pin = "1234"
        self.scores_buffer = [1.0] * 5
        
        # Behavioral tracking metrics
        self.dwells, self.flights = [], []
        self.mouse_x, self.mouse_y = [], []
        self.p_t = time.time()  # Initializing key press tracking matrix variable
        self.f_t = 0.0          # Initializing flight tracking matrix variable
        self.m_click_press = time.time() # Initializing mouse click matrix variable
        self.last_key_release = None
        self.last_mouse_time = time.time()
        self.last_x, self.last_y = 0, 0
        
        # Setup Database and AI Engine
        self.init_database()
        try:
            self.model = load_model('biokey_final_model.h5')
        except Exception as e:
            print(f"[WARN] AI Engine running in simulated mode. Missing model file. Error: {e}")
            self.model = None

        # Container for View Management
        self.container = tk.Frame(self, bg="#0a0a0a")
        self.container.pack(side="top", fill="both", expand=True)
        
        # Initialize Windows
        self.frames = {}
        for ViewClass in (LoginScreen, RegistrationScreen, SecurityDashboard):
            frame = ViewClass(parent=self.container, controller=self)
            self.frames[ViewClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_view(LoginScreen)

    def init_database(self):
        conn = sqlite3.connect('biokey_vault.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                          (username TEXT PRIMARY KEY, password TEXT, full_name TEXT)''')
        conn.commit()
        conn.close()

    def show_view(self, target_class):
        frame = self.frames[target_class]
        frame.tkraise()
        if target_class == SecurityDashboard:
            frame.on_activate()


# --- VIEW 1: AUTHENTICATION INTERFACE ---
class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#111111")
        self.controller = controller
        
        lbl = tk.Label(self, text="BIOMASS ACCESS ROUTER", font=("Courier", 24, "bold"), fg="#00ffcc", bg="#111111")
        lbl.pack(pady=40)
        
        tk.Label(self, text="Operator Username", fg="#888", bg="#111111", font=("Arial", 12)).pack()
        self.user_ent = tk.Entry(self, bg="#222", fg="#fff", insertbackground="white", width=30, font=("Arial", 12))
        self.user_ent.pack(pady=10)
        
        tk.Label(self, text="Secret Cipher Token", fg="#888", bg="#111111", font=("Arial", 12)).pack()
        self.pass_ent = tk.Entry(self, show="*", bg="#222", fg="#fff", insertbackground="white", width=30, font=("Arial", 12))
        self.pass_ent.pack(pady=10)
        
        btn_login = tk.Button(self, text="Authenticate", bg="#00ffcc", fg="#000", font=("Arial", 11, "bold"), width=20, command=self.attempt_login)
        btn_login.pack(pady=20)
        
        btn_reg = tk.Button(self, text="Enroll New Operator Profile", bg="#111", fg="#00ffcc", bd=0, command=lambda: controller.show_view(RegistrationScreen))
        btn_reg.pack()

    def attempt_login(self):
        username = self.user_ent.get().strip().lower()
        password = self.pass_ent.get().strip()
        
        # Structural Backdoor for Demo Safety
        if username == "mona" and password == "12345678":
            self.controller.active_user = "Mohana Priya"
            self.controller.show_view(SecurityDashboard)
            return
            
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect('biokey_vault.db')
        c = conn.cursor()
        c.execute("SELECT full_name FROM users WHERE username=? AND password=?", (username, hashed))
        row = c.fetchone()
        conn.close()
        
        if row:
            self.controller.active_user = row[0]
            self.controller.show_view(SecurityDashboard)
        else:
            messagebox.showerror("Access Denied", "Cryptographic failure: Invalid Credentials.")


# --- VIEW 2: RECRUITMENT & ENROLLMENT ---
class RegistrationScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#111111")
        self.controller = controller
        
        tk.Label(self, text="PROFILE ENROLLMENT MODULE", font=("Courier", 22, "bold"), fg="#00ffcc", bg="#111111").pack(pady=30)
        
        fields = [("Full Legal Name", "name"), ("Desired Identity Tag", "user"), ("Security Password", "pass"), ("Confirm Password", "confirm")]
        self.entries = {}
        for label_text, key in fields:
            tk.Label(self, text=label_text, fg="#888", bg="#111111").pack()
            show_char = "*" if "pass" in key or "confirm" in key else None
            ent = tk.Entry(self, show=show_char, bg="#222", fg="#fff", insertbackground="white", width=35)
            ent.pack(pady=5)
            self.entries[key] = ent
            
        tk.Button(self, text="Register & Build Profile", bg="#00ffcc", fg="#000", font=("Arial", 11, "bold"), command=self.register_operator).pack(pady=20)
        tk.Button(self, text="Return to Login", bg="#111", fg="#888", bd=0, command=lambda: controller.show_view(LoginScreen)).pack()

    def register_operator(self):
        name = self.entries["name"].get().strip()
        username = self.entries["user"].get().strip().lower()
        pwd = self.entries["pass"].get().strip()
        confirm = self.entries["confirm"].get().strip()
        
        if not (name and username and pwd):
            messagebox.showerror("Error", "All operational data layers must be populated.")
            return
        if pwd != confirm:
            messagebox.showerror("Error", "Password matrices do not converge.")
            return
            
        hashed = hashlib.sha256(pwd.encode()).hexdigest()
        try:
            conn = sqlite3.connect('biokey_vault.db')
            c = conn.cursor()
            c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hashed, name))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Profile built. Behavioral DNA capturing initialized.")
            self.controller.show_view(LoginScreen)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Identity Tag already reserved.")


# --- VIEW 3: MULTIMODAL PRODUCTION DASHBOARD ---
class SecurityDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#0a0a0a")
        self.controller = controller
        
        # Left Panel (Analytics Matrix)
        self.left_panel = tk.Frame(self, bg="#111111", width=250)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(self.left_panel, text="BIOMETRIC FEED", fg="#00ffcc", bg="#111111", font=("Courier", 12, "bold")).pack(pady=20)
        self.user_badge = tk.Label(self.left_panel, text="OPERATOR: NULL", fg="#fff", bg="#111111", font=("Arial", 10))
        self.user_badge.pack(pady=10)
        
        # HIGH-VALUE LAB ADDITION: Manual Emergency Panic Kill-Switch
        tk.Label(self.left_panel, text="TACTICAL OVERRIDES", fg="#555", bg="#111111", font=("Arial", 9, "bold")).pack(pady=30)
        btn_panic = tk.Button(self.left_panel, text="FORCE LOCKDOWN", bg="#ff3333", fg="#fff", font=("Arial", 10, "bold"), width=18, command=self.trigger_manual_panic)
        btn_panic.pack(pady=5)
        
        # Right Main Control Room
        self.right_panel = tk.Frame(self, bg="#0a0a0a")
        self.right_panel.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        self.banner = tk.Label(self.right_panel, text="INITIALIZING DEFENSE...", font=("Courier", 20, "bold"), fg="#fff", bg="#0a0a0a")
        self.banner.pack(pady=15)
        
        self.score_lbl = tk.Label(self.right_panel, text="Confidence Vector: Evaluating...", font=("Arial", 14), fg="#00ffcc", bg="#0a0a0a")
        self.score_lbl.pack()
        
        self.progress = ttk.Progressbar(self.right_panel, length=600, mode='determinate')
        self.progress.pack(pady=10)
        
        # Forensic Logging Window
        self.console = scrolledtext.ScrolledText(self.right_panel, height=8, bg="#000", fg="#00ff55", font=("Consolas", 9))
        self.console.pack(padx=20, pady=10, fill=tk.X)
        
        # Dual-Insight Visual Panel (Matplotlib Object Canvas)
        self.fig, (self.ax_key, self.ax_mouse) = plt.subplots(1, 2, figsize=(7, 3), facecolor="#0a0a0a")
        for ax in (self.ax_key, self.ax_mouse):
            ax.set_facecolor("#0a0a0a")
            ax.tick_params(colors='white', labelsize=8)
        self.ax_key.set_title("Keystroke Dynamics", color="#00ffcc", fontsize=9)
        self.ax_mouse.set_title("Mouse Trajectory Speed", color="#ffaa00", fontsize=9)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

    def on_activate(self):
        self.user_badge.config(text=f"OPERATOR:\n{self.controller.active_user.upper()}")
        self.banner.config(text="IDENTITY VERIFIED: SYSTEM LIVE", fg="#00ffcc")
        self.console.insert(tk.END, f"[SYSTEM STARTUP] Hooking multi-modal execution vectors for {self.controller.active_user}\n")
        
        # Initiate Asynchronous Structural Hooks
        self.key_hook = keyboard.Listener(on_press=self.process_keydown, on_release=self.process_keyup)
        self.mouse_hook = mouse.Listener(on_move=self.process_mousemove, on_click=self.process_mouseclick)
        
        self.key_hook.start()
        self.mouse_hook.start()

    def process_keydown(self, key):
        self.controller.p_t = time.time()
        self.controller.f_t = self.controller.p_t - self.controller.last_key_release if self.controller.last_key_release else 0

    def process_keyup(self, key):
        if self.controller.is_locked: return
        r_t = time.time()
        self.controller.last_key_release = r_t
        dwell = r_t - self.controller.p_t
        
        # Feature Matrix Pipeline Execution
        if self.controller.model:
            tensor = np.array([[dwell, self.controller.f_t]]).reshape(-1, 1, 2)
            raw_eval = self.controller.model.predict(tensor, verbose=0)[0][0]
            score = np.power(raw_eval, 10)
        else:
            # Optimized Simulator logic: realistic typing parameters to prevent chaotic false positives
            score = 0.99 if dwell < 0.40 else 0.35 
            
        self.controller.scores_buffer.append(score)
        if len(self.controller.scores_buffer) > 5: self.controller.scores_buffer.pop(0)
        
        # Data Synchronization for Analytics
        self.controller.dwells.append(dwell * 1000)
        self.controller.flights.append(self.controller.f_t * 1000)
        if len(self.controller.dwells) > 30: self.controller.dwells.pop(0); self.controller.flights.pop(0)
        
        self.refresh_defense_state(np.mean(self.controller.scores_buffer) * 100)

    def process_mousemove(self, x, y):
        if self.controller.is_locked: return
        t_curr = time.time()
        dt = t_curr - self.controller.last_mouse_time
        
        if dt > 0.01:  # Filter noise at 10ms sampling steps
            dist = np.sqrt((x - self.controller.last_x)**2 + (y - self.controller.last_y)**2)
            velocity = dist / dt
            
            self.controller.mouse_x.append(t_curr)
            self.controller.mouse_y.append(velocity)
            if len(self.controller.mouse_x) > 40: self.controller.mouse_x.pop(0); self.controller.mouse_y.pop(0)
            
            # Identify behavioral jitter thresholds
            if velocity > 7500:
                self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] [MOUSE JITTER ALERT] Extreme velocity signature: {velocity:.0f} px/sec\n")
                self.console.see(tk.END)
                self.refresh_defense_state(np.mean(self.controller.scores_buffer)*100 - 15)
                
            self.controller.last_x, self.controller.last_y = x, y
            self.controller.last_mouse_time = t_curr

    def process_mouseclick(self, x, y, button, pressed):
        if self.controller.is_locked: return
        if pressed:
            self.controller.m_click_press = time.time()
        else:
            m_dwell = time.time() - self.controller.m_click_press
            self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] [MOUSE DYNAMICS] Click dwell matrix registered: {m_dwell*1000:.1f}ms\n")
            self.console.see(tk.END)

    def refresh_defense_state(self, confidence_metric):
        # HARD GUARD: If already locked, drop incoming data immediately
        if self.controller.is_locked: 
            return
            
        if confidence_metric < 0: confidence_metric = 0
        if confidence_metric > 100: confidence_metric = 100
        
        self.score_lbl.config(text=f"Confidence Vector: {confidence_metric:.2f}%")
        self.progress['value'] = confidence_metric
        
        if confidence_metric >= 93.0:
            self.banner.config(text="IDENTITY VERIFIED: MONITORING LOCK GREEN", fg="#00ffcc")
        else:
            self.banner.config(text="CRITICAL THREAT INTRUSION DETECTED", fg="#ff3333")
            if not self.controller.alert_sent:
                self.controller.alert_sent = True
                self.controller.is_locked = True # Activate the thread guard barrier instantly
                
                # Asynchronously dispatch email without blocking
                threading.Thread(target=self.dispatch_forensic_email, args=(confidence_metric,)).start()
                
                # SAFELY schedule the lockdown interface to load on the MAIN UI thread loop
                self.controller.after(10, self.engage_lockdown_protocol)
                return 
                
        # Draw Realtime Statistical Visuals
        self.ax_key.clear()
        self.ax_mouse.clear()
        self.ax_key.set_title("Keystroke Dynamics (Dwell vs Flight)", color="#00ffcc", fontsize=8)
        self.ax_mouse.set_title("Mouse Trajectory Velocity Trend", color="#ffaa00", fontsize=8)
        
        if self.controller.dwells:
            self.ax_key.scatter(self.controller.dwells, self.controller.flights, color="#00ffcc", s=10)
        if self.controller.mouse_x:
            self.ax_mouse.plot(self.controller.mouse_y, color="#ffaa00", linewidth=1.5)
            
        self.canvas.draw()
    def dispatch_forensic_email(self, violation_score):
        try:
            msg = EmailMessage()
            msg.set_content(f"ALERT: System access breached for user: {self.controller.active_user}.\nConfidence index hit floor threshold: {violation_score:.2f}%\nTimestamp: {time.asctime()}")
            msg['Subject'] = "CRITICAL METRIC EXCLUSION: BioKey Breach Alert"
            msg['From'] = SMTP_USER
            msg['To'] = ALERT_RECEIVER
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as mailserver:
                mailserver.login(SMTP_USER, SMTP_PASS)
                mailserver.send_message(msg)
        except Exception as err:
            print(f"[ERR] Mail dispatch architecture timed out: {err}")

    def trigger_manual_panic(self):
        """High-Value Feature: Lets you drop the score manually to showcase the locking system instantly!"""
        self.refresh_defense_state(45.0)

    def engage_lockdown_protocol(self):
        # Now running safely on the Main Thread—Matplotlib can render and dialogs can draw!
        response = sd.askstring("BioKey Zero-Trust Isolation", "Anomaly detected in input fusion. Enter Operator PIN Token:", show='*')
        
        if response == self.controller.emergency_pin:
            # 1. Clear the structural blocking flags
            self.controller.is_locked = False
            self.controller.alert_sent = False
            
            # 2. FLUSH THE MEMORY BUFFERS COMPLETELY
            self.controller.scores_buffer = [1.0] * 5
            self.controller.dwells.clear()
            self.controller.flights.clear()
            self.controller.mouse_x.clear()
            self.controller.mouse_y.clear()
            
            # Reset tracking coordinates to avoid immediate layout updates
            self.controller.last_x, self.controller.last_y = self.winfo_pointerxy()
            self.controller.last_mouse_time = time.time()
            
            # 3. FORCE REFRESH VISUAL ELEMENT LAYOUTS
            self.banner.config(text="IDENTITY VERIFIED: RE-ESTABLISHING PROFILE", fg="#00ffcc")
            self.score_lbl.config(text="Confidence Vector: 100.00%")
            self.progress['value'] = 100
            
            self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] [RECOVERY SUCCESS] Challenge Token Verified. System state flushed.\n")
            self.console.see(tk.END)
            
            # Redraw a clean slate plot container layout instantly
            self.ax_key.clear()
            self.ax_mouse.clear()
            self.ax_key.set_title("Keystroke Dynamics (Dwell vs Flight)", color="#00ffcc", fontsize=8)
            self.ax_mouse.set_title("Mouse Trajectory Velocity Trend", color="#ffaa00", fontsize=8)
            self.canvas.draw()
            
            self.update_idletasks()
        else:
            # If PIN is wrong, re-trigger modal after a brief pause safely
            messagebox.showerror("Access Denied", "Invalid Security Token. Session remains isolated.")
            self.controller.after(200, self.engage_lockdown_protocol)
if __name__ == "__main__":
    app = BioKeyEnterpriseApp()
    app.mainloop()