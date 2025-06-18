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
import time
import re

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
FRAME_RATE = 30  # Frames per second for video capture
QUIT_KEY = keyboard.Key.esc  # Press ESC to quit
ENTER_KEY = keyboard.Key.enter  # Enter key to trigger screenshot

screen_width, screen_height = pyautogui.size()
fourcc = cv2.VideoWriter_fourcc(*"XVID")
out = cv2.VideoWriter(VIDEO_FILE, fourcc, FRAME_RATE, (screen_width, screen_height))

# Flag to indicate when to stop the program
stop_program = False

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

def sanitize_filename(filename):
    """Remove invalid characters for filenames."""
    return re.sub(r"[<>:\"/\\|?*]", "_", filename)

def log_event(event_type, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_message = f"[{timestamp}] {event_type}: {details}\n"
    with open(LOG_FILE, "a") as file:
        file.write(log_message)
    print(log_message, end="")

def save_screenshot(event_description):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
    sanitized_event = sanitize_filename(event_description)
    screenshot_filename = f"{timestamp}_{sanitized_event}.png"
    screenshot_path = os.path.join(SCREENSHOT_FOLDER, screenshot_filename)
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    log_event("Screenshot", f"{event_description}: Saved {screenshot_path}")

# Mouse event handlers
def on_click(x, y, button, pressed):
    if pressed:
        event_description = f"Mouse_Click_at_{x}_{y}_Button_{button}"
        log_event("Mouse Click", f"Button {button} at ({x}, {y})")
        save_screenshot(event_description)

# Keyboard event handlers
def on_press(key):
    global stop_program
    if key == QUIT_KEY:
        stop_program = True
        log_event("Quit", "Program terminated by user.")
        return False  # Stop the keyboard listener
    elif key == ENTER_KEY:
        log_event("Key Press", "Enter key pressed")
        save_screenshot("Enter_Key_Press")

# Monitor active window title change
def monitor_active_window():
    global stop_program
    last_window = None
    while not stop_program:
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

# Screen recording function
def record_screen():
    global stop_program
    while not stop_program:
        # Capture the screen continuously for video
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        time.sleep(1 / FRAME_RATE)

# Main function
def main():
    global stop_program
    # Start screen recording in a separate thread
    screen_thread = threading.Thread(target=record_screen, daemon=True)
    screen_thread.start()

    # Start mouse listener
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    # Start keyboard listener
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

    # Start active window monitoring
    active_window_thread = threading.Thread(target=monitor_active_window, daemon=True)
    active_window_thread.start()

    # Wait for the quit signal
    keyboard_listener.join()

    # Stop everything
    stop_program = True
    mouse_listener.stop()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
