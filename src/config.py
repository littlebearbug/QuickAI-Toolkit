# src/config.py

# --- Settings File ---
SETTINGS_FILE_PATH = "settings.json"

# --- Hotkey Configuration ---
HOTKEY_AUTO_COPY = '<ctrl>+<alt>+q'
HOTKEY_MANUAL_COPY = '<ctrl>+<alt>+c' 

# --- UI Configuration ---
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 380
UI_THEME = "dark-blue"
UI_APPEARANCE = "System" # "System", "Light", "Dark"
WINDOW_ALPHA = 0.96  # Window transparency (0.0 to 1.0)

# --- NEW: UI Style Constants ---
BORDER_COLOR = "#4A4A4A"
CLOSE_BUTTON_HOVER_COLOR = "#c42b1c"
SETTINGS_BUTTON_HOVER_COLOR = "#3E3E3E"
STATUS_TEXT_COLOR = "#9A9A9A"

TRANSLATION_TARGETS = [
    ("翻译为中文", "Simplified Chinese"),
    ("Translate to English", "English"),
    ("日本語に翻訳", "Japanese"),
    ("Traduire en Français", "French"),
    ("번역하기", "Korean"),
]