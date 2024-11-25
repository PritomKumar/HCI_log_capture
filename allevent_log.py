import time
import psutil
import win32gui
import win32process
from pynput import mouse, keyboard
from datetime import datetime


# Log file
LOG_FILE = "system_events.log"

def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    window_title = win32gui.GetWindowText(hwnd)
    return process.name(), window_title

def log_event(event_type, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Truncate to milliseconds
    log_message = f"[{timestamp}] {event_type}: {details}\n"
    with open(LOG_FILE, "a") as file:
        file.write(log_message)
    print(log_message, end="")  # Also print to the console if needed  

# Mouse event handlers
def on_click(x, y, button, pressed):
    if pressed:
        log_event("Mouse Click", f"Button {button} at ({x}, {y})")

def on_move(x, y):
    pass
    # log_event("Mouse Move", f"Position ({x}, {y})")

# Keyboard event handlers
def on_press(key):
    pass
    # try:
    #     log_event("Key Press", f"Key {key.char}")
    # except AttributeError:
    #     log_event("Key Press", f"Special Key {key}")

# Monitor active window title change
def monitor_active_window():
    last_window = None
    while True:
        current_process, current_window = get_active_window_title()
        if current_window != last_window:
            log_event("Window Switch", f"Process: {current_process}, Title: {current_window}")
            last_window = current_window
        time.sleep(1)

# Start logging events
def main():
    # Start mouse listener
    mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
    mouse_listener.start()

    # Start keyboard listener
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

    # Start active window monitoring
    monitor_active_window()

    # Wait for the listeners to stop (this will run indefinitely)
    mouse_listener.join()
    keyboard_listener.join()

if __name__ == "__main__":
    main()
