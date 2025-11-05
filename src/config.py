# src/config.py

# --- API and Model Configuration ---
API_URL = "http://localhost:11434/v1/chat/completions"
MODEL_NAME = "granite4:latest" # or "qwen2:7b", "llama3:8b", etc.

# --- Hotkey Configuration ---
# Plan A: Automatically copy selected text and show UI
HOTKEY_AUTO_COPY = '<ctrl>+<alt>+q'
# Plan B: Show UI for manually copied text
HOTKEY_MANUAL_COPY = '<ctrl>+<alt>+c' 

# --- UI Configuration ---
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 350
UI_THEME = "dark-blue" # "blue", "green"
UI_APPEARANCE = "System" # "System", "Light", "Dark"