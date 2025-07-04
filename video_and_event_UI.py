import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import pyautogui
import psutil
import win32gui
import win32process
from pynput import mouse, keyboard
from datetime import datetime
from screeninfo import get_monitors
import threading
import os
import re
import time

# Create a log folder
LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)


# File paths
current_timestamp = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
print(f"Current timestamp: {current_timestamp}")
LOG_FOLDER = os.path.join(LOG_FOLDER, current_timestamp)

LOG_FILE = os.path.join(LOG_FOLDER, "system_events.log")
VIDEO_FILE = os.path.join(LOG_FOLDER, "screen_recording.avi")
SCREENSHOT_FOLDER = os.path.join(LOG_FOLDER, "screenshots")
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

# Screen capture settings
FRAME_RATE = 10  # Frames per second for video capture
screen_width, screen_height = pyautogui.size()
fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter(VIDEO_FILE, fourcc, FRAME_RATE, (screen_width, screen_height))

# Global variables
stop_program = False
recording = False

def sanitize_filename(filename):
    """Remove invalid characters for filenames."""
    return re.sub(r"[<>:\"/\\|?*]", "_", filename)

def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    app_name = process.name()
    window_title = win32gui.GetWindowText(hwnd)

    # Get window position and determine monitor
    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    x_center = (rect[0] + rect[2]) // 2
    y_center = (rect[1] + rect[3]) // 2
    monitors = get_monitors()

    # Determine monitor number
    monitor_number = 0
    for i, monitor in enumerate(monitors, start=1):
        if monitor.x <= x_center < monitor.x + monitor.width and \
           monitor.y <= y_center < monitor.y + monitor.height:
            monitor_number = i
            break

    return app_name, window_title, monitor_number

def sanitize_unicode(text):
    """
    Replace non-ASCII characters in the text with a space.
    """
    return ''.join(char if ord(char) < 128 else ' ' for char in text)

def log_event(event_type, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    sanitized_details = sanitize_unicode(details)
    log_message = f"[{timestamp}] {event_type}: {sanitized_details}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_message)
    print(log_message, end="")

def save_screenshot(event_description):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
    sanitized_event = sanitize_filename(event_description)
    sanitized_details = sanitize_unicode(sanitized_event)
    screenshot_filename = f"{timestamp}_{sanitized_details}.png"
    # screenshot_filename = f"{timestamp}.png"
    screenshot_path = os.path.join(SCREENSHOT_FOLDER, screenshot_filename)
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    log_event("Screenshot", f"{event_description}: Saved {screenshot_path}")

# Mouse and Keyboard Event Handlers
def on_click(x, y, button, pressed):
    if pressed and recording:
        event_description = f"Mouse_Click_at_{x}_{y}_Button_{button}"
        log_event("Mouse Click", f"Button {button} at ({x}, {y})")
        save_screenshot(event_description)

def monitor_active_window():
    global stop_program
    last_window = None
    while not stop_program and recording:
        app_name, window_title, monitor_number = get_active_window_info()
        current_window = f"{app_name} | {window_title} | Monitor {monitor_number}"
        if current_window != last_window:
            event_description = f"Window_Switch_{app_name}_Monitor_{monitor_number}"
            log_event(
                "Window Switch",
                f"Active Application: {app_name}, Window Title: {window_title}, Monitor: {monitor_number}"
            )
            save_screenshot(event_description)
            last_window = current_window
        time.sleep(1)

def record_screen():
    global stop_program
    while not stop_program and recording:
        # Capture the screen continuously for video
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        time.sleep(1 / FRAME_RATE)

# Start and Stop Functions
def start_recording():
    global recording, stop_program
    if not recording:
        stop_program = False
        recording = True
        threading.Thread(target=record_screen, daemon=True).start()
        threading.Thread(target=monitor_active_window, daemon=True).start()
        mouse_listener.start()
        log_event("Start", "Recording started.")

def stop_recording():
    global recording, stop_program
    if recording:
        recording = False
        stop_program = True
        mouse_listener.stop()
        log_event("Stop", "Recording stopped.")
        out.release()
        messagebox.showinfo("Info", "Recording stopped successfully!")

# Create UI
def create_ui():
    window = tk.Tk()
    window.title("Screen Recorder")
    window.geometry("300x150")
    window.resizable(False, False)

    label = tk.Label(window, text="Screen Recorder", font=("Arial", 16))
    label.pack(pady=10)

    start_button = tk.Button(window, text="Start Recording", font=("Arial", 12), bg="green", fg="white",
                              command=start_recording)
    start_button.pack(pady=5)

    stop_button = tk.Button(window, text="Stop Recording", font=("Arial", 12), bg="red", fg="white",
                             command=stop_recording)
    stop_button.pack(pady=5)

    window.mainloop()

# Main Function
if __name__ == "__main__":
    mouse_listener = mouse.Listener(on_click=on_click)
    create_ui()
