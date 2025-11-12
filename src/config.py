# src/config.py

# --- Settings File ---
SETTINGS_FILE_PATH = "settings.json"

# --- Hotkey Configuration ---
HOTKEY_AUTO_COPY = '<ctrl>+<alt>+q'
HOTKEY_MANUAL_COPY = '<ctrl>+<alt>+c' 

# --- UI Configuration ---
WINDOW_ALPHA = 0.96          # Window transparency (0.0 to 1.0)
UI_THEME = "dark-blue"
UI_APPEARANCE = "System"     # "System", "Light", "Dark"

# --- NEW: Dynamic UI Layout Constants ---
TOOLBAR_HEIGHT = 50
PANEL_MAX_HEIGHT = 200
WINDOW_WIDTH = 450
CORNER_RADIUS = 16
BUTTON_SIZE = 32

# --- NEW: Animation Constants ---
ANIMATION_DURATION_MS = 200  # Animation duration in milliseconds
ANIMATION_FRAMES = 30        # Number of frames for the animation

# --- NEW: Colors & Icons ---
# A color that will be made transparent. Choose something unlikely to be used.
TRANSPARENT_COLOR = '#000001' 
# Use a tuple for light/dark mode colors
TOOLBAR_BG_COLOR = ("#F2F3F5", "#2B2D30") 
PANEL_BG_COLOR = ("#F2F3F5", "#2B2D30")
CLOSE_BUTTON_HOVER_COLOR = "#c42b1c"
COPY_BUTTON_HOVER_COLOR = "#3E3E3E"
TRANSLATION_BUTTON_COLOR = ("#2B2D30", "#F2F3F5")

# --- Icon Paths (ensure these files exist in assets/) ---
ICON_PATHS = {
    "translate": "assets/translate.png",
    "polish": "assets/polish.png",
    "summarize": "assets/summarize.png",
    "settings": "assets/settings.png",
    "close_app": "assets/close.png",
    "close_panel": "assets/close.png", # Can reuse icons
    "copy": "assets/copy.png",
}

# --- Translation Targets ---
TRANSLATION_TARGETS = [
    ("翻译为中文", "Simplified Chinese"),
    ("Translate to English", "English"),
    ("日本語に翻訳", "Japanese"),
]