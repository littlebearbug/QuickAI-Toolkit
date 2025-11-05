# src/clipboard_handler.py

import ctypes
import time
import pyperclip
from ctypes import wintypes

# --- WinAPI Definitions ---
user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_C = 0x43

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("ii", Input_I)]

def _send_input(inputs):
    n_inputs = len(inputs)
    lp_input = (Input * n_inputs)(*inputs)
    cb_size = ctypes.sizeof(Input)
    return user32.SendInput(n_inputs, lp_input, cb_size)

def _press_key(hex_key_code):
    x = Input(type=INPUT_KEYBOARD,
              ii=Input_I(ki=KeyBdInput(wVk=hex_key_code)))
    _send_input([x])

def _release_key(hex_key_code):
    x = Input(type=INPUT_KEYBOARD,
              ii=Input_I(ki=KeyBdInput(wVk=hex_key_code, dwFlags=KEYEVENTF_KEYUP)))
    _send_input([x])

def get_selected_text_auto() -> str | None:
    """
    Saves original clipboard, simulates Ctrl+C, gets text, and restores clipboard.
    Returns the captured text, or None if it fails.
    """
    original_clipboard = pyperclip.paste()
    pyperclip.copy('')
    
    try:
        _press_key(VK_CONTROL)
        _press_key(VK_C)
        time.sleep(0.05)
        _release_key(VK_C)
        _release_key(VK_CONTROL)
        
        # Wait for the clipboard to be updated by the OS
        time.sleep(0.1)
        
        selected_text = pyperclip.paste()
        return selected_text if selected_text else None
        
    finally:
        # Restore the original clipboard content
        pyperclip.copy(original_clipboard)