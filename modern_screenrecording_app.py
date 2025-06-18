import tkinter as tk
from tkinter import messagebox, filedialog, ttk, scrolledtext
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
import subprocess
import sys

# Global variables
recording = False
stop_program = False
out = None
recording_session = 0
recording_folder = None
screenshots_folder = None
videos_folder = None
log_file_path = None

FRAME_RATE = 10
screen_width, screen_height = pyautogui.size()
fourcc = cv2.VideoWriter_fourcc(*"XVID")

# UI Theme Colors - Colorblind Friendly & Accessible
COLORS = {
    'bg_primary': '#1E1E2E',        # Deep navy - primary background
    'bg_secondary': '#2A2A3E',      # Lighter navy - secondary panels
    'bg_tertiary': '#363654',       # Medium purple-gray - cards
    'accent_primary': '#89DCEB',    # Soft cyan - primary actions
    'accent_secondary': '#CBA6F7',  # Soft purple - secondary actions
    'success': '#A6E3A1',          # Soft green - success states
    'warning': '#F9E2AF',          # Soft yellow - warnings
    'danger': '#F38BA8',           # Soft pink - errors/stop
    'info': '#94E2D5',             # Soft teal - information
    'text_primary': '#CDD6F4',     # Light blue-white - primary text
    'text_secondary': '#BAC2DE',   # Medium blue-gray - secondary text
    'text_muted': '#9399B2',       # Muted blue-gray - subtle text
    'border_light': '#45475A',     # Light border
    'border_dark': '#313244',      # Dark border
    'surface': '#181825'           # Input/surface backgrounds
}

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

    rect = win32gui.GetWindowRect(hwnd)
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
    global recording_session, videos_folder
    recording_session += 1
    return os.path.join(videos_folder, f"recording_{recording_session}.avi")

def initialize_folders():
    global recording_folder, screenshots_folder, videos_folder, log_file_path

    recording_folder = filedialog.askdirectory(title="Select Folder for Recordings")
    if not recording_folder:
        messagebox.showerror("Error", "Recording folder not selected. Please try again.")
        return False

    DATA_FOLDER = "recording_logs"
    current_timestamp = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
    DATA_FOLDER = os.path.join(DATA_FOLDER, current_timestamp)
    recording_folder = os.path.join(recording_folder, DATA_FOLDER)

    screenshots_folder = os.path.join(recording_folder, "screenshots")
    videos_folder = os.path.join(recording_folder, "videos")
    log_folder = os.path.join(recording_folder, "logs")
    os.makedirs(screenshots_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)
    os.makedirs(log_folder, exist_ok=True)

    log_file_path = os.path.join(log_folder, "system_events.log")
    return True

class ModernScreenRecorder:
    def __init__(self):
        self.window = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.update_ui_state()
        
        # Threading variables
        self.mouse_listener = None
        self.active_window_thread = None
        self.screen_record_thread = None
        
    def setup_window(self):
        self.window.title("🎬 Experiment Screen Recorder")
        self.window.geometry("500x650")
        self.window.resizable(True, True)
        self.window.configure(bg=COLORS['bg_primary'])
        
        # Start maximized (full screen)
        self.window.state('zoomed')  # Windows
        try:
            self.window.attributes('-zoomed', True)  # Linux
        except:
            pass
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('Header.TLabel', 
                           background=COLORS['bg_primary'], 
                           foreground=COLORS['text_primary'],
                           font=('Segoe UI', 18, 'bold'))
        
        self.style.configure('Status.TLabel',
                           background=COLORS['bg_primary'],
                           foreground=COLORS['text_secondary'],
                           font=('Segoe UI', 12))
        
        self.style.configure('Info.TLabel',
                           background=COLORS['bg_tertiary'],
                           foreground=COLORS['text_primary'],
                           font=('Segoe UI', 10, 'bold'))

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.window, bg=COLORS['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🧪 Experiment Recorder", 
                               style='Header.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, 
                                  text="Capture screen, interactions & system events",
                                  style='Status.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Status Card
        status_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'], 
                               relief=tk.FLAT, bd=0)
        status_frame.pack(fill=tk.X, pady=(0, 20), padx=0, ipady=20)
        
        # Add subtle border effect
        border_frame = tk.Frame(status_frame, bg=COLORS['border_light'], height=1)
        border_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_title = ttk.Label(status_frame, text="📊 Recording Status", 
                                style='Info.TLabel')
        status_title.pack(pady=(15, 8))
        
        self.status_label = tk.Label(status_frame, text="● Not Recording", 
                                    font=('Segoe UI', 16, 'bold'),
                                    bg=COLORS['bg_tertiary'], 
                                    fg=COLORS['text_muted'])
        self.status_label.pack(pady=(0, 8))
        
        self.session_label = tk.Label(status_frame, text="Session: 0", 
                                     font=('Segoe UI', 11),
                                     bg=COLORS['bg_tertiary'], 
                                     fg=COLORS['text_secondary'])
        self.session_label.pack(pady=(0, 15))
        
        # Control Buttons Frame
        controls_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Start/Stop buttons
        self.start_button = tk.Button(controls_frame, text="▶ Start Recording",
                                     font=('Segoe UI', 12, 'bold'),
                                     bg=COLORS['success'], fg=COLORS['bg_primary'],
                                     activebackground=COLORS['success'],
                                     activeforeground=COLORS['bg_primary'],
                                     relief=tk.FLAT, padx=20, pady=12,
                                     cursor='hand2',
                                     command=self.start_recording)
        self.start_button.pack(fill=tk.X, pady=(0, 12))
        
        self.stop_button = tk.Button(controls_frame, text="⏹ Stop Recording",
                                    font=('Segoe UI', 12, 'bold'),
                                    bg=COLORS['danger'], fg=COLORS['bg_primary'],
                                    activebackground=COLORS['danger'],
                                    activeforeground=COLORS['bg_primary'],
                                    relief=tk.FLAT, padx=20, pady=12,
                                    cursor='hand2',
                                    command=self.stop_recording,
                                    state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=(0, 12))
        
        # Utility buttons
        utils_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        utils_frame.pack(fill=tk.X, pady=(0, 20))
        
        utils_title = ttk.Label(utils_frame, text="🔧 Utilities", 
                               style='Info.TLabel')
        utils_title.pack(pady=(0, 10))
        
        # Row 1: View Log and Open Folder
        utils_row1 = tk.Frame(utils_frame, bg=COLORS['bg_primary'])
        utils_row1.pack(fill=tk.X, pady=(0, 5))
        
        self.log_button = tk.Button(utils_row1, text="📋 View Log",
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=COLORS['accent_primary'], fg=COLORS['bg_primary'],
                                   activebackground=COLORS['accent_primary'],
                                   activeforeground=COLORS['bg_primary'],
                                   relief=tk.FLAT, padx=15, pady=10,
                                   cursor='hand2',
                                   command=self.view_log,
                                   state=tk.DISABLED)
        self.log_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        self.folder_button = tk.Button(utils_row1, text="📁 Open Folder",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=COLORS['warning'], fg=COLORS['bg_primary'],
                                      activebackground=COLORS['warning'],
                                      activeforeground=COLORS['bg_primary'],
                                      relief=tk.FLAT, padx=15, pady=10,
                                      cursor='hand2',
                                      command=self.open_folder,
                                      state=tk.DISABLED)
        self.folder_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        # Settings Frame
        settings_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'], 
                                 relief=tk.FLAT, bd=0)
        settings_frame.pack(fill=tk.X, pady=(0, 20), padx=0, ipady=15)
        
        # Add subtle border effect
        border_frame2 = tk.Frame(settings_frame, bg=COLORS['border_light'], height=1)
        border_frame2.pack(fill=tk.X, side=tk.BOTTOM)
        
        settings_title = ttk.Label(settings_frame, text="⚙️ Settings", 
                                  style='Info.TLabel')
        settings_title.pack(pady=(15, 15))
        
        # Frame rate setting
        fps_frame = tk.Frame(settings_frame, bg=COLORS['bg_tertiary'])
        fps_frame.pack(fill=tk.X, padx=25, pady=(0, 15))
        
        fps_label = tk.Label(fps_frame, text="Frame Rate (FPS):", 
                            font=('Segoe UI', 11, 'bold'),
                            bg=COLORS['bg_tertiary'], 
                            fg=COLORS['text_primary'])
        fps_label.pack(side=tk.LEFT)
        
        self.fps_var = tk.StringVar(value=str(FRAME_RATE))
        fps_spinbox = tk.Spinbox(fps_frame, from_=1, to=30, width=12,
                                textvariable=self.fps_var,
                                font=('Segoe UI', 11),
                                bg=COLORS['surface'],
                                fg=COLORS['text_primary'],
                                buttonbackground=COLORS['accent_secondary'],
                                selectbackground=COLORS['accent_primary'],
                                insertbackground=COLORS['text_primary'],
                                relief=tk.FLAT,
                                bd=1,
                                command=self.update_frame_rate)
        fps_spinbox.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bind Enter key to update frame rate
        fps_spinbox.bind('<Return>', lambda event: self.update_frame_rate())
        fps_spinbox.bind('<FocusOut>', lambda event: self.update_frame_rate())
        
        # Info Panel
        info_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'], 
                             relief=tk.FLAT, bd=0)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 10))
        
        # Add subtle border effect
        border_frame3 = tk.Frame(info_frame, bg=COLORS['border_light'], height=1)
        border_frame3.pack(fill=tk.X, side=tk.BOTTOM)
        
        info_title = ttk.Label(info_frame, text="ℹ️ Session Info", 
                              style='Info.TLabel')
        info_title.pack(pady=(15, 10))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8,
                                                  font=('JetBrains Mono', 10),
                                                  bg=COLORS['surface'], 
                                                  fg=COLORS['text_primary'],
                                                  insertbackground=COLORS['accent_primary'],
                                                  selectbackground=COLORS['accent_secondary'],
                                                  selectforeground=COLORS['bg_primary'],
                                                  relief=tk.FLAT,
                                                  bd=0,
                                                  state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Add initial info
        self.add_info("🚀 Screen Recorder initialized")
        self.add_info(f"📺 Screen resolution: {screen_width}x{screen_height}")
        self.add_info("📝 Click 'Start Recording' to begin experiment")

    def add_info(self, message):
        """Add timestamped info to the info panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.info_text.config(state=tk.DISABLED)
        self.info_text.see(tk.END)

    def update_frame_rate(self):
        """Update global frame rate from spinbox"""
        global FRAME_RATE
        try:
            FRAME_RATE = int(self.fps_var.get())
            self.add_info(f"⚙️ Frame rate updated to {FRAME_RATE} FPS")
        except ValueError:
            pass

    def update_ui_state(self):
        """Update UI elements based on recording state"""
        if recording:
            self.status_label.config(text="● Recording Active", fg=COLORS['success'])
            self.start_button.config(state=tk.DISABLED, 
                                   bg=COLORS['text_muted'],
                                   fg=COLORS['bg_secondary'])
            self.stop_button.config(state=tk.NORMAL,
                                  bg=COLORS['danger'],
                                  fg=COLORS['bg_primary'])
            self.session_label.config(text=f"Session: {recording_session}")
        else:
            self.status_label.config(text="● Not Recording", fg=COLORS['text_muted'])
            self.start_button.config(state=tk.NORMAL,
                                   bg=COLORS['success'],
                                   fg=COLORS['bg_primary'])
            self.stop_button.config(state=tk.DISABLED,
                                  bg=COLORS['text_muted'],
                                  fg=COLORS['bg_secondary'])
            
        # Enable utility buttons if we have a recording folder
        if recording_folder:
            self.log_button.config(state=tk.NORMAL,
                                 bg=COLORS['accent_primary'],
                                 fg=COLORS['bg_primary'])
            self.folder_button.config(state=tk.NORMAL,
                                    bg=COLORS['warning'],
                                    fg=COLORS['bg_primary'])
        else:
            self.log_button.config(state=tk.DISABLED,
                                 bg=COLORS['text_muted'],
                                 fg=COLORS['bg_secondary'])
            self.folder_button.config(state=tk.DISABLED,
                                    bg=COLORS['text_muted'],
                                    fg=COLORS['bg_secondary'])

    def start_recording(self):
        global recording, stop_program, out
        
        if not recording:
            # Initialize folders on first recording session
            if recording_folder is None and not initialize_folders():
                return
            
            stop_program = False
            recording = True
            
            # Update UI
            self.update_ui_state()
            self.add_info("🎬 Recording started!")
            
            # Initialize video writer for the new session
            video_filename = get_next_video_filename()
            out = cv2.VideoWriter(video_filename, fourcc, FRAME_RATE, (screen_width, screen_height))
            
            # Start threads
            self.mouse_listener = mouse.Listener(on_click=on_click)
            self.mouse_listener.start()
            
            self.active_window_thread = threading.Thread(target=monitor_active_window, daemon=True)
            self.active_window_thread.start()
            
            self.screen_record_thread = threading.Thread(target=record_screen, daemon=True)
            self.screen_record_thread.start()
            
            log_event("Start", f"Recording started: {video_filename}")
            self.add_info(f"💾 Saving to: recording_{recording_session}.avi")

    def stop_recording(self):
        global recording, stop_program, out
        
        if recording:
            recording = False
            stop_program = True
            
            # Update UI
            self.update_ui_state()
            self.add_info("⏹ Recording stopped!")
            
            # Stop mouse listener and threads
            if self.mouse_listener:
                self.mouse_listener.stop()
            
            log_event("Stop", f"Recording stopped. Saved as recording_{recording_session}.avi")
            out.release()
            
            self.add_info(f"✅ Session {recording_session} saved successfully!")
            messagebox.showinfo("Recording Complete", 
                              f"Recording saved as recording_{recording_session}.avi!")

    def view_log(self):
        """Open log file in a new window"""
        if not log_file_path or not os.path.exists(log_file_path):
            messagebox.showwarning("Warning", "Log file not found!")
            return
            
        # Create log viewer window
        log_window = tk.Toplevel(self.window)
        log_window.title("📋 System Events Log")
        log_window.geometry("800x600")
        log_window.configure(bg=COLORS['bg_primary'])
        
        # Start log window maximized (full screen)
        log_window.state('zoomed')  # Windows
        try:
            log_window.attributes('-zoomed', True)  # Linux
        except:
            pass
        
        # Log content frame
        log_frame = tk.Frame(log_window, bg=COLORS['bg_primary'], padx=20, pady=20)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = tk.Label(log_frame, text="📊 System Events Log", 
                               font=('Segoe UI', 18, 'bold'),
                               bg=COLORS['bg_primary'], fg=COLORS['text_primary'])
        header_label.pack(pady=(0, 20))
        
        # Log text area
        log_text = scrolledtext.ScrolledText(log_frame, 
                                           font=('JetBrains Mono', 11),
                                           bg=COLORS['surface'], 
                                           fg=COLORS['text_primary'],
                                           insertbackground=COLORS['accent_primary'],
                                           selectbackground=COLORS['accent_secondary'],
                                           selectforeground=COLORS['bg_primary'],
                                           relief=tk.FLAT,
                                           bd=0)
        log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Load and display log content
        try:
            with open(log_file_path, 'r', encoding='utf-8') as file:
                log_content = file.read()
                log_text.insert(tk.END, log_content)
                log_text.config(state=tk.DISABLED)
        except Exception as e:
            log_text.insert(tk.END, f"Error reading log file: {str(e)}")
            log_text.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = tk.Frame(log_frame, bg=COLORS['bg_primary'])
        buttons_frame.pack(fill=tk.X)
        
        refresh_btn = tk.Button(buttons_frame, text="🔄 Refresh",
                               font=('Segoe UI', 11, 'bold'),
                               bg=COLORS['info'], fg=COLORS['bg_primary'],
                               activebackground=COLORS['info'],
                               activeforeground=COLORS['bg_primary'],
                               relief=tk.FLAT, padx=20, pady=10,
                               cursor='hand2',
                               command=lambda: self.refresh_log(log_text))
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        close_btn = tk.Button(buttons_frame, text="✕ Close",
                             font=('Segoe UI', 11, 'bold'),
                             bg=COLORS['accent_secondary'], fg=COLORS['bg_primary'],
                             activebackground=COLORS['accent_secondary'],
                             activeforeground=COLORS['bg_primary'],
                             relief=tk.FLAT, padx=20, pady=10,
                             cursor='hand2',
                             command=log_window.destroy)
        close_btn.pack(side=tk.RIGHT)

    def refresh_log(self, log_text_widget):
        """Refresh the log content in the viewer"""
        log_text_widget.config(state=tk.NORMAL)
        log_text_widget.delete(1.0, tk.END)
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as file:
                log_content = file.read()
                log_text_widget.insert(tk.END, log_content)
        except Exception as e:
            log_text_widget.insert(tk.END, f"Error reading log file: {str(e)}")
        
        log_text_widget.config(state=tk.DISABLED)
        log_text_widget.see(tk.END)

    def open_folder(self):
        """Open the recording folder in file explorer"""
        if not recording_folder or not os.path.exists(recording_folder):
            messagebox.showwarning("Warning", "Recording folder not found!")
            return
            
        try:
            if sys.platform == "win32":
                os.startfile(recording_folder)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", recording_folder])
            else:  # Linux
                subprocess.run(["xdg-open", recording_folder])
            
            self.add_info("📁 Recording folder opened")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def run(self):
        """Start the application"""
        self.add_info("🎯 Ready for experiments!")
        self.window.mainloop()

# Main Function
if __name__ == "__main__":
    app = ModernScreenRecorder()
    app.run()