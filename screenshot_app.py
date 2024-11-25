import os
import time
from datetime import datetime
import threading
import mss
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Default directory to save screenshots
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)
chosen_directory = save_dir

# Global variables for controlling the screenshot-taking process
is_running = False
capture_interval = 2  # Default interval in seconds

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

def take_screenshots():
    global chosen_directory
    with mss.mss() as sct:
        active_window_title = get_active_window_title()
        print(f"Active Window: {active_window_title}")

        for monitor_number, monitor in enumerate(sct.monitors[1:], start=1):
            if monitor_number == 2:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sanitized_title = sanitize_filename(active_window_title)
                filename = os.path.join(chosen_directory, f"screenshot_monitor{monitor_number}_{sanitized_title}_{timestamp}.png")
                
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                print(f"Screenshot saved: {filename}")

def screenshot_loop():
    while is_running:
        take_screenshots()
        time.sleep(capture_interval)

def start_screenshots():
    global is_running, chosen_directory
    if not is_running:
        # Ask the user to choose a directory to save screenshots
        chosen_directory = filedialog.askdirectory(title="Select Save Location") or save_dir
        os.makedirs(chosen_directory, exist_ok=True)
        is_running = True
        threading.Thread(target=screenshot_loop, daemon=True).start()
        messagebox.showinfo("Screenshot Capture", f"Screenshots will be saved to: {chosen_directory}")

def stop_screenshots():
    global is_running
    is_running = False

def update_interval(event):
    global capture_interval
    capture_interval = int(interval_var.get())

# GUI setup
root = tk.Tk()
root.title("Screenshot Capture App")

# Start and Stop buttons
start_button = tk.Button(root, text="Start", command=start_screenshots)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop", command=stop_screenshots)
stop_button.pack(pady=10)

# Dropdown for selecting capture frequency
interval_var = tk.StringVar(value="2")
interval_label = tk.Label(root, text="Capture Frequency (seconds):")
interval_label.pack(pady=5)

interval_dropdown = ttk.Combobox(root, textvariable=interval_var, values=["1", "2", "5", "10", "30", "60"])
interval_dropdown.bind("<<ComboboxSelected>>", update_interval)
interval_dropdown.pack(pady=10)

# Run the GUI
root.mainloop()

# age, familiarity, gender, how often you use chatgpt,  SUS questions, UEQ, UES, NASA-TLX, 
