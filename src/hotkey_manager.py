import threading
from pynput import keyboard
from src import config

def start_listener(auto_callback, manual_callback):
    """
    Starts the global hotkey listener in a separate daemon thread.
    """
    def run_listener():
        hotkeys = {
            config.HOTKEY_AUTO_COPY: auto_callback,
            config.HOTKEY_MANUAL_COPY: manual_callback
        }
        with keyboard.GlobalHotKeys(hotkeys) as listener:
            print("--- QuickAI-Toolkit is Running ---")
            print(f"[Auto-Copy Mode] Press '{config.HOTKEY_AUTO_COPY}' to capture selected text.")
            print(f"[Manual-Copy Mode] Manually copy text, then press '{config.HOTKEY_MANUAL_COPY}'.")
            print("For auto-copy to work, the app may need Administrator rights.")
            listener.join()

    listener_thread = threading.Thread(target=run_listener, daemon=True)
    listener_thread.start()