import pymem
import pymem.process
import keyboard
import time
import os
import ctypes
import tkinter as tk

# --- APP INFO ---
VERSION = "1.03"
GITHUB_URL = "https://github.com/bableg/OutOfOre-AutoLeveler"
PROCESS_NAME = "OutOfOre-Win64-Shipping.exe"

# --- CONFIGURATION ---
KEYS = {"LEFT": 0x4B, "RIGHT": 0x4D, "UP": 0x48, "DOWN": 0x50} 
TOLERANCE_ANGLE = 0.10 
TOLERANCE_GPS = 0.5 

# --- MEMORY OFFSETS ---
BASE_GPS = 0x05901438
OFFSETS_GPS = [0xF8, 0x48, 0x50, 0xC0, 0x350, 0x260, 0x9C] 
BASE_ANGLE = 0x05D8B018 
OFFSETS_ANGLE = [0x10, 0x110, 0x258, 0x870, 0x2F0, 0x260, 0xF8] # ROLL
OFFSETS_PITCH = [0x10, 0x110, 0x258, 0x870, 0x2F0, 0x260, 0x118] # PITCH 

user32 = ctypes.windll.user32

class OverlayUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BABLEG_OVL")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.config(bg="black")
        self.root.geometry("350x200+50+50") # for shadow
        
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0, bd=0)
        self.canvas.pack(expand=True, fill="both")
        
        self.shadow = self.canvas.create_text(12, 12, anchor="nw", text="INITIALIZING...", 
                                              font=("Consolas", 10, "bold"), fill="#111111")
        self.text = self.canvas.create_text(10, 10, anchor="nw", text="INITIALIZING...", 
                                            font=("Consolas", 10, "bold"), fill="#00FF00")
        
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)

    def update(self, text_content):
        self.canvas.itemconfig(self.shadow, text=text_content)
        self.canvas.itemconfig(self.text, text=text_content)
        self.root.update()

def send_key(scancode, duration):
    try:
        user32.keybd_event(0, scancode, 0x0008, 0)
        time.sleep(duration)
        user32.keybd_event(0, scancode, 0x0008 | 0x0002, 0)
    except: pass

def get_dynamic_hold(diff, is_gps=False):
    mult = 0.003 if is_gps else 0.04
    max_hold = 0.15 if is_gps else 0.12
    return max(0.02, min(abs(diff) * mult, max_hold))

class AutoPilot:
    def __init__(self, ui):
        self.ui = ui
        self.pm = None
        self.module_base = None
        self.mode_list = ["OFF", "GPS_LEVEL", "FULL_AUTO", "SEMI_AUTO"]
        self.mode_idx = 0
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
            return True
        except:
            self.is_connected = False
            return False

    def get_addr(self, base_offset, offsets):
        if not self.is_connected: return None
        try:
            addr = self.pm.read_longlong(self.module_base + base_offset)
            for offset in offsets[:-1]:
                addr = self.pm.read_longlong(addr + offset)
            return addr + offsets[-1]
        except: return None 

    def run(self):
        if not self.is_connected:
            if not self.connect():
                msg = " [!] SEARCHING FOR GAME..."
                self.ui.update(msg)
                print(msg, end="\r")
                return

        addr_roll = self.get_addr(BASE_ANGLE, OFFSETS_ANGLE)
        addr_pitch = self.get_addr(BASE_ANGLE, OFFSETS_PITCH)
        addr_gps = self.get_addr(BASE_GPS, OFFSETS_GPS)

        # Inputs
        if keyboard.is_pressed('f9'):
            self.mode_idx = (self.mode_idx + 1) % len(self.mode_list)
            if addr_gps:
                try: self.target_gps = round(self.pm.read_float(addr_gps), -1)
                except: pass
            time.sleep(0.3)

        if keyboard.is_pressed('f4'):
            self.mode_idx = 0
            time.sleep(0.2)

        try:
            cur_s = self.pm.read_float(addr_roll) if addr_roll else 0.0
            cur_p = self.pm.read_float(addr_pitch) if addr_pitch else 0.0
            raw_g = self.pm.read_float(addr_gps) if addr_gps else 0.0
            if raw_g != 0: self.last_valid_gps = raw_g
            cur_g = self.last_valid_gps

            mode = self.mode_list[self.mode_idx]
            telemetry = (
                f"=== AutoLeveler v{VERSION} ===\n"
                f"=== github.com/bableg/OutOfOre-AutoLeveler ===\n"
                f"MODE: {mode}\n"
                f"{'-'*30}\n"
                f"ROLL : {cur_s:7.2f} | Tgt Roll: {self.target_side:7.2f}\n"
                f"PITCH: {cur_p:7.2f} | Tgt Pitch: {self.target_pitch:7.2f}\n"
                f"DEPTH: {int(cur_g):7} | Tgt Depth: {int(self.target_gps):7}\n"
                f"{'-'*30}\n"
                f"F9: Mode | F4: Emergency Stop" )

            self.ui.update(telemetry)
            print("\033[H", end="")
            print(telemetry.replace("\n", "\n ")) 

            # Autoleveler inputs
            if mode != "OFF":
                # Manual Adj
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

                # Send Keys
                diff_s = cur_s - self.target_side
                if abs(diff_s) > TOLERANCE_ANGLE:
                    send_key(KEYS["LEFT" if diff_s < 0 else "RIGHT"], get_dynamic_hold(diff_s))

                if mode == "GPS_LEVEL":
                    diff_g = cur_g - self.target_gps
                    if abs(diff_g) >= TOLERANCE_GPS:
                        send_key(KEYS["DOWN" if diff_g > 0 else "UP"], get_dynamic_hold(diff_g, True))
                elif mode == "FULL_AUTO":
                    diff_p = cur_p - self.target_pitch
                    if abs(diff_p) > TOLERANCE_ANGLE:
                        send_key(KEYS["DOWN" if diff_p > 0 else "UP"], get_dynamic_hold(diff_p))

        except Exception:
            self.is_connected = False

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    ovl = OverlayUI()
    bot = AutoPilot(ovl)
    
    while True:
        bot.run()
        if keyboard.is_pressed('end'):
            break
        time.sleep(0.01)
