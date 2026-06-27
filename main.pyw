import pymem
import pymem.process
import keyboard
import time
import os
import sys
import ctypes
import json
import tkinter as tk
from tkinter import ttk
import webbrowser

# --- APP INFO ---
VERSION = "1.05"
GITHUB_URL = "https://github.com/bableg/OutOfOre-AutoLeveler"
PROCESS_NAME = "OutOfOre-Win64-Shipping.exe"

# --- CONFIG PATH ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "autolevel_config.json")

# --- MEMORY OFFSETS ---

BASE_ANGLE = 0x05D8B018
OFFSETS_ANGLE = [0x10, 0x110, 0x258, 0x870, 0x2F0, 0x260, 0xF8]
OFFSETS_PITCH = [0x10, 0x110, 0x258, 0x870, 0x2F0, 0x260, 0x118]
OFFSETS_GPS = [0x10, 0x110, 0x258, 0x870, 0x2F0, 0x260, 0x128]

KEYS = {"LEFT": 0x4B, "RIGHT": 0x4D, "UP": 0x48, "DOWN": 0x50}
user32 = ctypes.windll.user32

def send_key(scancode, duration):
    try:
        user32.keybd_event(0, scancode, 0x0008, 0)
        time.sleep(duration)
        user32.keybd_event(0, scancode, 0x0008 | 0x0002, 0)
    except:
        pass

# --- UI SETUP ---
class MainUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"AutoLeveler Control Panel v{VERSION}")
        self.root.geometry("400x520")
        self.root.attributes("-topmost", True)
        
        # Load Config
        self.config = self.load_config()
        
        self.angle_tol = tk.DoubleVar(value=self.config.get("angle_tol", 0.10))
        self.gps_tol = tk.DoubleVar(value=self.config.get("gps_tol", 0.50))
        self.speed_mult = tk.DoubleVar(value=self.config.get("speed_mult", 1.0))
        
        self.setup_control_panel()

        # In-Game Overlay (Top-Left)
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-transparentcolor", "black")
        self.overlay.config(bg="black")
        self.overlay.geometry("350x200+50+50")
        
        self.canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0, bd=0)
        self.canvas.pack(expand=True, fill="both")
        self.shadow = self.canvas.create_text(12, 12, anchor="nw", text="INITIALIZING...", font=("Consolas", 10, "bold"), fill="#111111")
        self.text = self.canvas.create_text(10, 10, anchor="nw", text="INITIALIZING...", font=("Consolas", 10, "bold"), fill="#00FF00")
        
        hwnd = ctypes.windll.user32.GetParent(self.overlay.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_settings(self):
        config_data = {
            "angle_tol": self.angle_tol.get(),
            "gps_tol": self.gps_tol.get(),
            "speed_mult": self.speed_mult.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            self.lbl_status.config(text="Status: SETTINGS SAVED ✓", foreground="blue")
        except:
            self.lbl_status.config(text="Status: FAILED TO SAVE!", foreground="red")

    def setup_control_panel(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"))
        style.configure("Link.TLabel", font=("Segoe UI", 9, "underline"), foreground="#1a73e8")
        style.configure("Brand.TLabel", font=("Segoe UI", 9, "bold"), foreground="#555555")

        # Telemetry Frame
        frame_tel = ttk.LabelFrame(self.root, text=" Telemetry Data ")
        frame_tel.pack(padx=10, pady=10, fill="x")

        self.lbl_status = ttk.Label(frame_tel, text="Status: SEARCHING FOR GAME...", foreground="red")
        self.lbl_status.pack(anchor="w", padx=5, pady=2)
        
        self.lbl_mode = ttk.Label(frame_tel, text="Mode: OFF", font=("Segoe UI", 10, "bold"))
        self.lbl_mode.pack(anchor="w", padx=5, pady=2)

        # Re-detect Game Button
        self.btn_reconnect = ttk.Button(frame_tel, text="🔄 Re-detect Game", style="Action.TButton")
        self.btn_reconnect.pack(anchor="w", padx=5, pady=5)

        self.lbl_data = ttk.Label(frame_tel, text="Roll: 0.00 | Pitch: 0.00\nDepth: 0", justify="left", font=("Consolas", 10))
        self.lbl_data.pack(anchor="w", padx=5, pady=5)

        # Settings Frame (Sliders)
        frame_set = ttk.LabelFrame(self.root, text=" Settings ")
        frame_set.pack(padx=10, pady=5, fill="both", expand=True)

        ttk.Label(frame_set, text="Angle Tolerance:").pack(anchor="w", padx=5, pady=(8, 0))
        self.scale_angle = ttk.Scale(frame_set, from_=0.01, to=0.50, variable=self.angle_tol, orient="horizontal")
        self.scale_angle.pack(fill="x", padx=5, pady=2)
        self.lbl_angle_val = ttk.Label(frame_set, text=f"{self.angle_tol.get():.2f}")
        self.lbl_angle_val.pack(anchor="e", padx=5)

        ttk.Label(frame_set, text="GPS Depth Tolerance:").pack(anchor="w", padx=5)
        self.scale_gps = ttk.Scale(frame_set, from_=0.1, to=5.0, variable=self.gps_tol, orient="horizontal")
        self.scale_gps.pack(fill="x", padx=5, pady=2)
        self.lbl_gps_val = ttk.Label(frame_set, text=f"{self.gps_tol.get():.2f}")
        self.lbl_gps_val.pack(anchor="e", padx=5)

        ttk.Label(frame_set, text="Reaction Speed (Multiplier):").pack(anchor="w", padx=5)
        self.scale_speed = ttk.Scale(frame_set, from_=0.1, to=3.0, variable=self.speed_mult, orient="horizontal")
        self.scale_speed.pack(fill="x", padx=5, pady=2)
        self.lbl_speed_val = ttk.Label(frame_set, text=f"{self.speed_mult.get():.2f}x")
        self.lbl_speed_val.pack(anchor="e", padx=5)

        self.scale_angle.configure(command=lambda e: self.lbl_angle_val.config(text=f"{self.angle_tol.get():.2f}"))
        self.scale_gps.configure(command=lambda e: self.lbl_gps_val.config(text=f"{self.gps_tol.get():.2f}"))
        self.scale_speed.configure(command=lambda e: self.lbl_speed_val.config(text=f"{self.speed_mult.get():.2f}x"))

        # Save Button
        self.btn_save = ttk.Button(frame_set, text="💾 Save Settings", command=self.save_settings)
        self.btn_save.pack(pady=10)

        # --- BRANDING & LINKS ---
        frame_brand = ttk.Frame(self.root)
        frame_brand.pack(pady=10, fill="x")

        lbl_github = ttk.Label(frame_brand, text="GitHub Repository", style="Link.TLabel", cursor="hand2")
        lbl_github.pack(anchor="center")
        lbl_github.bind("<Button-1>", lambda e: webbrowser.open_new(GITHUB_URL))

        lbl_powered = ttk.Label(frame_brand, text="powered by BABLEG", style="Brand.TLabel")
        lbl_powered.pack(anchor="center", pady=2)

        # Exit Button
        ttk.Button(self.root, text="Exit Application (END)", command=self.root.quit).pack(pady=5)

    def update_overlay(self, text_content):
        self.canvas.itemconfig(self.shadow, text=text_content)
        self.canvas.itemconfig(self.text, text=text_content)

    def update_panel(self, status, mode, telemetry_text, is_connected):
        if "SAVED" not in self.lbl_status.cget("text") and "FAILED" not in self.lbl_status.cget("text"):
            self.lbl_status.config(text=status, foreground="green" if is_connected else "red")
        
        self.lbl_mode.config(text=f"Mode: {mode}")
        self.lbl_data.config(text=telemetry_text)

# --- AUTOPILOT LOGIC ---
class AutoPilot:
    def __init__(self, ui):
        self.ui = ui
        self.pm = None
        self.module_base = None
        self.mode_list = ["OFF", "GPS_LEVEL", "FULL_AUTO", "SEMI_AUTO"]
        self.mode_idx = 0
        self.saved_mode_idx = 1 
        self.target_side = 0.0
        self.target_pitch = 0.0
        self.target_gps = 0.0
        self.last_valid_gps = 0.0
        self.is_connected = False

    def connect(self):
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            self.module_base = pymem.process.module_from_name(self.pm.process_handle, PROCESS_NAME).lpBaseOfDll
            self.is_connected = True
            self.ui.lbl_status.config(text="Status: CONNECTED", foreground="green") # Reset save msg
            return True
        except: 
            self.is_connected = False
            return False

    def force_reconnect(self):
        self.is_connected = False
        self.pm = None
        self.module_base = None
        self.ui.lbl_status.config(text="Status: RE-DETECTING...", foreground="orange")
        self.connect()

    def get_addr(self, base_offset, offsets):
        if not self.is_connected: return None
        try:
            addr = self.pm.read_longlong(self.module_base + base_offset)
            for offset in offsets[:-1]:
                addr = self.pm.read_longlong(addr + offset)
            return addr + offsets[-1]
        except: return None 

    def get_dynamic_hold(self, diff, is_gps=False, speed_mult=1.0):
        mult = (0.003 if is_gps else 0.04) * speed_mult
        max_hold = (0.15 if is_gps else 0.12) * speed_mult
        return max(0.02, min(abs(diff) * mult, max_hold))

    def run(self):
        if not self.is_connected:
            if not self.connect():
                msg = " [!] SEARCHING FOR GAME..."
                self.ui.update_overlay(msg)
                self.ui.update_panel("Status: SEARCHING FOR GAME...", "OFF", "N/A", False)
                return

        addr_roll = self.get_addr(BASE_ANGLE, OFFSETS_ANGLE)
        addr_pitch = self.get_addr(BASE_ANGLE, OFFSETS_PITCH)
        addr_gps = self.get_addr(BASE_ANGLE, OFFSETS_GPS)

        if keyboard.is_pressed('f9'):
            self.mode_idx = (self.mode_idx + 1) % len(self.mode_list)
            if self.mode_idx != 0:
                self.saved_mode_idx = self.mode_idx 
            if addr_gps:
                try: self.target_gps = round(self.pm.read_float(addr_gps), -1)
                except: pass
            time.sleep(0.3)

        if keyboard.is_pressed('f4'):
            if self.mode_idx != 0:
                self.saved_mode_idx = self.mode_idx 
                self.mode_idx = 0
            else:
                self.mode_idx = self.saved_mode_idx 
            time.sleep(0.3)

        try:
            cur_s = self.pm.read_float(addr_roll) if addr_roll else 0.0
            cur_p = self.pm.read_float(addr_pitch) if addr_pitch else 0.0
            
            cur_g = None
            if addr_gps:
                try: cur_g = self.pm.read_float(addr_gps)
                except: pass
            
            if cur_g is None or cur_g == 0:
                cur_g = self.last_valid_gps
            else:
                self.last_valid_gps = cur_g

            mode = self.mode_list[self.mode_idx]
            
            overlay_text = (
                f"=== AutoLeveler v{VERSION} ===\n"
                f"MODE: {mode}\n"
                f"{'-'*30}\n"
                f"ROLL : {cur_s:7.2f} | Tgt Roll: {self.target_side:7.2f}\n"
                f"PITCH: {cur_p:7.2f} | Tgt Pitch: {self.target_pitch:7.2f}\n"
                f"DEPTH: {int(cur_g):7} | Tgt Depth: {int(self.target_gps):7}\n"
                f"{'-'*30}\n"
                f"F9: Mode | F4: Stop/Resume | 5: Reset Tgt" 
            )
            
            panel_data = (
                f"Roll : {cur_s:7.2f} | Target: {self.target_side:7.2f}\n"
                f"Pitch: {cur_p:7.2f} | Target: {self.target_pitch:7.2f}\n"
                f"Depth: {int(cur_g):7} | Target: {int(self.target_gps):7}"
            )

            self.ui.update_overlay(overlay_text)
            self.ui.update_panel("Status: CONNECTED", mode, panel_data, True)

            current_tol_angle = self.ui.angle_tol.get()
            current_tol_gps = self.ui.gps_tol.get()
            current_speed = self.ui.speed_mult.get()

            if mode != "OFF":
                if mode == "GPS_LEVEL":
                    if keyboard.is_pressed('f5'): self.target_gps -= 5.0; time.sleep(0.05)
                    if keyboard.is_pressed('f6'): self.target_gps += 5.0; time.sleep(0.05)
                elif mode == "FULL_AUTO":
                    if keyboard.is_pressed('f5'): self.target_pitch -= 0.05; time.sleep(0.1)
                    if keyboard.is_pressed('f6'): self.target_pitch += 0.05; time.sleep(0.1)

                if mode in ["FULL_AUTO", "SEMI_AUTO"]:
                    if keyboard.is_pressed('f7'): self.target_side -= 0.05; time.sleep(0.1)
                    if keyboard.is_pressed('f8'): self.target_side += 0.05; time.sleep(0.1)

                if keyboard.is_pressed('5'):
                    self.target_side = 0.0; self.target_pitch = 0.0
                    if mode == "GPS_LEVEL": self.target_gps = round(cur_g, -1)
                    time.sleep(0.2)

                diff_s = cur_s - self.target_side
                if abs(diff_s) > current_tol_angle:
                    send_key(KEYS["LEFT" if diff_s < 0 else "RIGHT"], self.get_dynamic_hold(diff_s, False, current_speed))

                if mode == "GPS_LEVEL":
                    diff_g = cur_g - self.target_gps
                    if abs(diff_g) >= current_tol_gps:
                        send_key(KEYS["DOWN" if diff_g > 0 else "UP"], self.get_dynamic_hold(diff_g, True, current_speed))
                elif mode == "FULL_AUTO":
                    diff_p = cur_p - self.target_pitch
                    if abs(diff_p) > current_tol_angle:
                        send_key(KEYS["DOWN" if diff_p > 0 else "UP"], self.get_dynamic_hold(diff_p, False, current_speed))

        except Exception:
            self.is_connected = False

# --- MAIN LOOP HANDLER ---
def run_app():
    app_ui = MainUI()
    bot = AutoPilot(app_ui)
    
    app_ui.btn_reconnect.config(command=bot.force_reconnect)

    def bot_loop():
        if keyboard.is_pressed('end'):
            app_ui.root.quit()
            return
        
        bot.run()
        app_ui.root.after(10, bot_loop)

    app_ui.root.after(10, bot_loop)
    app_ui.root.mainloop()

if __name__ == "__main__":
    run_app()
