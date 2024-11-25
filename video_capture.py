import os
import threading
import numpy as np
import cv2
import mss
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time

# Default directory to save videos
save_dir = "videos"
os.makedirs(save_dir, exist_ok=True)
chosen_directory = save_dir

# Global variables for controlling the video capture process
is_running = False

def sanitize_filename(title):
    # Replace any character not alphanumeric or underscore with an underscore
    return re.sub(r'[^a-zA-Z0-9_]', '_', title)

def get_active_window_title():
    try:
        import pygetwindow as gw
        active_window = gw.getActiveWindow()
        return active_window.title if active_window else "Unknown Window"
    except Exception as e:
        print(f"Error fetching active window title: {e}")
        return "Error"

def start_video_capture():
    global is_running, chosen_directory
    if not is_running:
        # Ask the user to choose a directory to save videos
        chosen_directory = filedialog.askdirectory(title="Select Save Location") or save_dir
        os.makedirs(chosen_directory, exist_ok=True)
        is_running = True
        threading.Thread(target=video_capture_loop, daemon=True).start()
        messagebox.showinfo("Video Capture", f"Video will be saved to: {chosen_directory}")

def stop_video_capture():
    global is_running
    is_running = False

def video_capture_loop():
    global chosen_directory
    with mss.mss() as sct:
        monitor = sct.monitors[2]  # Capture from monitor 2 (change if needed)
        width, height = monitor['width'], monitor['height']
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(chosen_directory, f"screen_capture_{timestamp}.avi")
        out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))

        print(f"Recording video to {filename}...")
        while is_running:
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR
            out.write(img)

        out.release()
        print("Video capture stopped.")

# GUI setup
root = tk.Tk()
root.title("Screen Capture App")

# Start and Stop buttons
start_button = tk.Button(root, text="Start Video Capture", command=start_video_capture)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Video Capture", command=stop_video_capture)
stop_button.pack(pady=10)

# Run the GUI
root.mainloop()
