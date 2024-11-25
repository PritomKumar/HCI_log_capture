import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import numpy as np
import pyautogui
import psutil
import win32gui
import win32process
from pynput import mouse
from datetime import datetime
from screeninfo import get_monitors
import threading
import os
import re
import time

# Global variables
recording = False
stop_program = False
out = None
recording_session = 0
recording_folder = None  # To store the user-selected folder for recordings
screenshots_folder = None
videos_folder = None
log_file_path = None

FRAME_RATE = 10 # change this to make the video smoother.
screen_width, screen_height = pyautogui.size()
fourcc = cv2.VideoWriter_fourcc(*"XVID")


def sanitize_filename(filename):
    """Remove invalid characters for filenames."""
    return re.sub(r"[<>:\"/\\|?*]", "_", filename)


def sanitize_unicode(text):
    """Replace non-ASCII characters with a space."""
    return ''.join(char if ord(char) < 128 else ' ' for char in text)


def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    app_name = process.name()
    window_title = win32gui.GetWindowText(hwnd)

    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    x_center = (rect[0] + rect[2]) // 2
    y_center = (rect[1] + rect[3]) // 2
    monitors = get_monitors()

    monitor_number = 0
    for i, monitor in enumerate(monitors, start=1):
        if monitor.x <= x_center < monitor.x + monitor.width and \
           monitor.y <= y_center < monitor.y + monitor.height:
            monitor_number = i
            break

    return app_name, window_title, monitor_number


def log_event(event_type, details):
    global log_file_path
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    sanitized_details = sanitize_unicode(details)
    log_message = f"[{timestamp}] {event_type}: {sanitized_details}\n"
    with open(log_file_path, "a", encoding="utf-8") as file:
        file.write(log_message)
    print(log_message, end="")


def save_screenshot(event_description):
    global screenshots_folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
    sanitized_event = sanitize_filename(event_description)
    screenshot_filename = f"{timestamp}_{sanitized_event}.png"
    screenshot_path = os.path.join(screenshots_folder, screenshot_filename)
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    log_event("Screenshot", f"{event_description}: Saved {screenshot_path}")


# Mouse Event Handlers
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
    global stop_program, out
    while not stop_program and recording:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        time.sleep(1 / FRAME_RATE)


def get_next_video_filename():
    """
    Generate the next video filename based on the recording session number.
    """
    global recording_session, videos_folder
    recording_session += 1
    return os.path.join(videos_folder, f"recording_{recording_session}.avi")


# Initialize Folders
def initialize_folders():
    global recording_folder, screenshots_folder, videos_folder, log_file_path

    # Ask user for folder
    recording_folder = filedialog.askdirectory(title="Select Folder for Recordings")
    if not recording_folder:
        messagebox.showerror("Error", "Recording folder not selected. Please try again.")
        return False

    # Create subfolders
    screenshots_folder = os.path.join(recording_folder, "screenshots")
    videos_folder = os.path.join(recording_folder, "videos")
    log_folder = os.path.join(recording_folder, "logs")
    os.makedirs(screenshots_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)
    os.makedirs(log_folder, exist_ok=True)

    # Set log file path
    log_file_path = os.path.join(log_folder, "system_events.log")
    return True


# Start and Stop Functions
def start_recording():
    global recording, stop_program, out, mouse_listener, active_window_thread, screen_record_thread

    if not recording:
        # Initialize folders on first recording session
        if recording_folder is None and not initialize_folders():
            return

        stop_program = False
        recording = True

        # Update UI
        status_label.config(text="Recording in Progress...", fg="green")

        # Initialize video writer for the new session
        video_filename = get_next_video_filename()
        out = cv2.VideoWriter(video_filename, fourcc, FRAME_RATE, (screen_width, screen_height))

        # Start threads
        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()

        active_window_thread = threading.Thread(target=monitor_active_window, daemon=True)
        active_window_thread.start()

        screen_record_thread = threading.Thread(target=record_screen, daemon=True)
        screen_record_thread.start()

        log_event("Start", f"Recording started: {video_filename}")


def stop_recording():
    global recording, stop_program, out, mouse_listener
    if recording:
        recording = False
        stop_program = True

        # Update UI
        status_label.config(text="Not Recording", fg="red")

        # Stop mouse listener and threads
        mouse_listener.stop()

        log_event("Stop", f"Recording stopped. Saved as recording_{recording_session}.avi")
        out.release()
        messagebox.showinfo("Info", f"Recording saved as recording_{recording_session}.avi!")


# Create UI
def create_ui():
    window = tk.Tk()
    window.title("Screen Recorder")
    window.geometry("300x200")
    window.resizable(False, False)

    global status_label
    status_label = tk.Label(window, text="Not Recording", font=("Arial", 12), fg="red")
    status_label.pack(pady=10)

    start_button = tk.Button(window, text="Start Recording", font=("Arial", 12), bg="green", fg="white",
                              command=start_recording)
    start_button.pack(pady=5)

    stop_button = tk.Button(window, text="Stop Recording", font=("Arial", 12), bg="red", fg="white",
                             command=stop_recording)
    stop_button.pack(pady=5)

    window.mainloop()


# Main Function
if __name__ == "__main__":
    create_ui()
