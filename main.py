# main.py

import customtkinter as ctk
from src.app import QuickAIToolkit
from src.config import UI_APPEARANCE, UI_THEME

def main():
    """
    Initializes and runs the QuickAI-Toolkit application.
    """
    ctk.set_appearance_mode(UI_APPEARANCE)
    ctk.set_default_color_theme(UI_THEME)
    
    root = ctk.CTk()
    app = QuickAIToolkit(root)
    root.mainloop()

if __name__ == "__main__":
    main()