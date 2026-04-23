# OutOfOre-AutoLeveler
**External GPS Autopilot and Blade Stabilization tool for Out of Ore (v0.34)**
** https://youtu.be/cilwSmtzddM **

---

## 🛠 v1.03 - Update Notes
This version introduces significant quality-of-life improvements and a brand-new visual interface for a more professional excavating experience.

### **What's New?**
* **External GUI Overlay:** A dedicated, transparent on-screen display (HUD) has been added.
    > **⚠️ Note:** For the overlay to function correctly, please set your game to **Windowed Borderless** mode.
* **Persistent Logic:** Targets for Pitch and Roll are now preserved in memory after pressing **F4 (Reset)**, allowing for quicker recalibration during complex maneuvers.
* **Emergency Stop Refactor:** The `ESC` key functionality has been redesigned for a smoother script termination process.
* **Performance Optimizations:** Under-the-hood refinements to memory polling frequency and CPU usage.

### **Credits**
Special thanks to our community on **Reddit, Discord, and YouTube** for the feedback and suggestions that made this update possible! 🥂

---

## 🛰️ Project Overview
This is an external automation tool that provides advanced blade stabilization and GPS-based depth management. It reads real-time memory telemetry and simulates key presses to maintain your target position with high precision.

### ⚠️ Critical Requirements & Warnings
* **GPS Receiver Module:** Your vehicle **MUST** have a GPS Receiver installed.
* ~~**Single Player Only:** Designed strictly for Single Player sessions.~~
* ~~**Session Bug:** If you join a Multiplayer server, memory addresses will conflict. **Restart the game** and enter Single Player directly.~~
* **Tested Vehicles:** Chariton DX11000 (Dozer) and Chariton g200E (Grader).

---

## 🚀 Key Features
* **GPS Level Mode:** Maintains a consistent centimeter-perfect depth.
* **Full Auto Mode:** Automatically stabilizes both **Blade Roll** and **Blade Pitch**.
* **Semi-Auto Mode:** Stabilizes **Blade Roll** only. **(Recommended for Graders)**.
* **Precision Adjustment:** Fine-tune targets with **0.05-degree** increments.

---

## ⌨️ Controls & Keybindings

| Key | Mode | Action | Step |
| :--- | :--- | :--- | :--- |
| **F9** | Global | **Switch Mode** (OFF -> GPS -> FULL -> SEMI) | - |
| **F4** | Global | **Emergency OFF** | - |
| **F5 / F6** | **GPS_LEVEL** | Decrease / Increase Target Depth | 5.0 cm |
| **F5 / F6** | **FULL_AUTO** | Lower / Lift Blade Pitch (Vertical) | 0.05° |
| **F7 / F8** | **Auto Modes**| Tilt Left / Right (Roll Angle) | 0.05° |
| **Num 5** | Global | **Reset/Sync:** 0.0 Angles or Sync GPS Depth | - |
| **ESC** | Global | **Exit Script** | - |

---

## 🛠️ Setup & Installation

1. Install [Python 3.10+](https://www.python.org/).
2. Install dependencies: `"pip install pymem"`
3. Install dependencies: `"pip install keyboard"`
4. Install dependencies: `"pip install tkinter"(Note: tkinter usually comes pre-installed with Python. If you see an error, it can be added via Python's "Modify" setup).`
5. Set in-game blade controls: **Num 8/2 (Up/Down)** and **Num 4/6 (Tilt)**.
6. Run the game, then launch the script as **Administrator**.
