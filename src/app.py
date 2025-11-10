# src/app.py

import customtkinter as ctk
import threading
import queue
import pyperclip
from src import config, prompts
from src.settings_manager import SettingsManager
from src.ai_clients import get_ai_client
from src.clipboard_handler import get_selected_text_auto
from src.hotkey_manager import start_listener

# SettingsWindow class remains unchanged from the previous version...
class SettingsWindow(ctk.CTkToplevel):
    """A popup window for configuring AI providers and settings."""
    def __init__(self, parent, settings_manager: SettingsManager):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.parent_app = parent

        self.title("Settings")
        self.geometry("400x350")
        self.transient(parent)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self.grid_columnconfigure(1, weight=1)
        
        # Provider Selection
        ctk.CTkLabel(self, text="AI Provider:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.provider_var = ctk.StringVar(value=self.settings_manager.get("current_provider"))
        self.provider_menu = ctk.CTkOptionMenu(self, variable=self.provider_var, 
                                               values=list(self.settings_manager.get("providers").keys()),
                                               command=self.on_provider_change)
        self.provider_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # API URL
        ctk.CTkLabel(self, text="API URL:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.api_url_var = ctk.StringVar()
        self.api_url_entry = ctk.CTkEntry(self, textvariable=self.api_url_var)
        self.api_url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Model Name
        ctk.CTkLabel(self, text="Model Name:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.model_name_var = ctk.StringVar()
        self.model_name_entry = ctk.CTkEntry(self, textvariable=self.model_name_var)
        self.model_name_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # API Key
        ctk.CTkLabel(self, text="API Key:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.api_key_var = ctk.StringVar()
        self.api_key_entry = ctk.CTkEntry(self, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        # Save Button
        save_button = ctk.CTkButton(self, text="Save and Close", command=self.save_and_close)
        save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20)

        self.on_provider_change(self.provider_var.get())
        self.withdraw()

    def on_provider_change(self, provider_name: str):
        provider_data = self.settings_manager.get("providers")[provider_name]
        self.api_url_var.set(provider_data.get("api_url", ""))
        self.model_name_var.set(provider_data.get("model_name", ""))
        self.api_key_var.set(provider_data.get("api_key", ""))
        self.api_key_entry.configure(state="normal" if provider_name != "Ollama" else "disabled")

    def save_and_close(self):
        current_settings = self.settings_manager.settings
        provider_name = self.provider_var.get()
        current_settings["current_provider"] = provider_name
        current_settings["providers"][provider_name] = {
            "api_url": self.api_url_var.get(), "model_name": self.model_name_var.get(), "api_key": self.api_key_var.get()
        }
        self.settings_manager.save_settings(current_settings)
        self.parent_app.reload_ai_client()
        self.withdraw()


class QuickAIToolkit:
    def __init__(self, root: ctk.CTk):
        # ... (init logic remains mostly the same) ...
        self.root = root
        self.root.withdraw()
        self.settings_manager = SettingsManager()
        self.ai_client = None
        self.reload_ai_client()
        self.selected_text = ""
        self.response_queue = queue.Queue()
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.lang_map = {display: prompt_lang for display, prompt_lang in config.TRANSLATION_TARGETS}
        self.translate_variable = ctk.StringVar(value="🌐 翻译") # NEW: Added icon
        self.popup_window = self._create_popup_window()
        self.settings_window = SettingsWindow(self.popup_window, self.settings_manager)
        start_listener(self.on_hotkey_activate_auto, self.on_hotkey_activate_manual)
        self.process_queue()
    
    # ... (reload_ai_client, drag handlers, hotkey handlers, etc. remain unchanged) ...
    def reload_ai_client(self):
        """Reloads the AI client based on the current settings."""
        provider_name = self.settings_manager.get("current_provider")
        provider_info = self.settings_manager.get_current_provider_info()
        self.ai_client = get_ai_client(provider_name, provider_info)
        print(f"AI Provider switched to: {provider_name} ({provider_info.get('model_name')})")
        if hasattr(self, 'status_label'):
             self.status_label.configure(text=f"{provider_name}: {provider_info.get('model_name')}")

    def on_drag_start(self, event):
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y

    def on_drag_motion(self, event):
        x = self.popup_window.winfo_pointerx() - self.drag_offset_x
        y = self.popup_window.winfo_pointery() - self.drag_offset_y
        self.popup_window.geometry(f"+{x}+{y}")
        
    def _create_popup_window(self) -> ctk.CTkToplevel:
        """Creates the completely redesigned popup window."""
        popup = ctk.CTkToplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.attributes("-alpha", config.WINDOW_ALPHA)
        popup.bind("<Escape>", self.hide_window)
        
        # Main container with a subtle border to create a "floating" effect
        main_container = ctk.CTkFrame(popup, corner_radius=12, border_width=1, border_color=config.BORDER_COLOR)
        main_container.pack(fill="both", expand=True, padx=2, pady=2)

        # --- 1. Header / Draggable Title Bar ---
        header = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        header.pack(side="top", fill="x", padx=10, pady=5)
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header, text="QuickAI Toolkit", font=ctk.CTkFont(size=13, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # RE-ADDED: Close button with modern styling
        close_button = ctk.CTkButton(header, text="✕", command=self.hide_window, width=28, height=28,
                                     fg_color="transparent", hover_color=config.CLOSE_BUTTON_HOVER_COLOR)
        close_button.grid(row=0, column=1, sticky="e")

        # Make header draggable
        header.bind("<ButtonPress-1>", self.on_drag_start)
        header.bind("<B1-Motion>", self.on_drag_motion)
        title_label.bind("<ButtonPress-1>", self.on_drag_start)
        title_label.bind("<B1-Motion>", self.on_drag_motion)
        
        # --- 2. Action Bar (Segmented Control Style) ---
        action_bar = ctk.CTkFrame(main_container, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=5)
        action_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.buttons = {
            "polish": ctk.CTkButton(action_bar, text="✨ 润色", command=lambda: self.start_ai_task("polish_text")),
            "summarize": ctk.CTkButton(action_bar, text="📜 总结", command=lambda: self.start_ai_task("summarize_points"))
        }
        self.buttons["polish"].grid(row=0, column=0, padx=(0, 2), sticky="ew")
        self.buttons["summarize"].grid(row=0, column=1, padx=2, sticky="ew")
        
        translation_menu = ctk.CTkOptionMenu(action_bar, variable=self.translate_variable,
                                               values=[display for display, _ in config.TRANSLATION_TARGETS],
                                               command=self.on_language_select, anchor="w")
        translation_menu.grid(row=0, column=2, padx=(2, 0), sticky="ew")
        
        # --- 3. Main Content (Feedback Area) ---
        self.feedback_textbox = ctk.CTkTextbox(main_container, wrap="word", state="disabled", 
                                               font=("Segoe UI", 14), corner_radius=8, border_width=0)
        self.feedback_textbox.pack(fill="both", expand=True, padx=10, pady=5)

        # --- 4. Footer ---
        footer = ctk.CTkFrame(main_container, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=10, pady=(5, 8))
        footer.grid_columnconfigure(0, weight=1)
        
        provider_info = self.settings_manager.get_current_provider_info()
        self.status_label = ctk.CTkLabel(footer, text=f"{self.settings_manager.get('current_provider')}: {provider_info.get('model_name')}",
                                         font=ctk.CTkFont(size=11), text_color=config.STATUS_TEXT_COLOR)
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # IMPROVED: Settings button with better visibility and hover effect
        settings_button = ctk.CTkButton(footer, text="⚙️", command=self.show_settings, width=28, height=28,
                                        fg_color="transparent", text_color="#C0C0C0",
                                        hover_color=config.SETTINGS_BUTTON_HOVER_COLOR)
        settings_button.grid(row=0, column=1, sticky="e")
        
        popup.withdraw()
        return popup

    def on_language_select(self, selected_display_name: str):
        prompt_language = self.lang_map.get(selected_display_name)
        if prompt_language:
            self.start_ai_task("translate", target_language=prompt_language)
        self.root.after(500, lambda: self.translate_variable.set("🌐 翻译"))

    def on_hotkey_activate_auto(self):
        self.root.after(0, self._activate_sequence, get_selected_text_auto)

    def on_hotkey_activate_manual(self):
        self.root.after(0, self._activate_sequence, pyperclip.paste)
        
    def _activate_sequence(self, text_getter):
        text = text_getter()
        if text and text.strip():
            self.selected_text = text
            self.show_window()
        else:
            print("Activation failed: No text captured.")
    
    def show_window(self):
        self._clear_feedback()
        x, y = self.root.winfo_pointerxy()
        self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x - 50}+{y - 20}")
        self.popup_window.deiconify()
        self.popup_window.lift()
        self.popup_window.focus_force()

    def show_settings(self):
        self.settings_window.deiconify()
        self.settings_window.lift()
        self.settings_window.focus_force()

    def hide_window(self, event=None):
        self.popup_window.withdraw()
        self.settings_window.withdraw()

    def start_ai_task(self, action: str, **kwargs):
        self._set_ui_state(is_busy=True)
        self._clear_feedback()
        messages = prompts.get_prompt_messages(action, self.selected_text, **kwargs)
        if messages:
            threading.Thread(target=self._run_ai_stream, args=(messages,), daemon=True).start()
        else:
            self._set_ui_state(is_busy=False)

    def _run_ai_stream(self, messages: list):
        try:
            for chunk in self.ai_client.stream_response(messages):
                self.response_queue.put(chunk)
        finally:
            self.response_queue.put(None)

    def process_queue(self):
        try:
            while not self.response_queue.empty():
                item = self.response_queue.get_nowait()
                if item is None:
                    self._set_ui_state(is_busy=False)
                else:
                    self.feedback_textbox.configure(state="normal")
                    self.feedback_textbox.insert("end", item)
                    self.feedback_textbox.see("end")
                    self.feedback_textbox.configure(state="disabled")
        finally:
            self.root.after(100, self.process_queue)
    
    def _set_ui_state(self, is_busy: bool):
        state = "disabled" if is_busy else "normal"
        # Disable all buttons and the option menu in the action bar
        action_bar = self.buttons["polish"].master
        for widget in action_bar.winfo_children():
            widget.configure(state=state)

    def _clear_feedback(self):
        self.feedback_textbox.configure(state="normal")
        self.feedback_textbox.delete("1.0", "end")
        self.feedback_textbox.configure(state="disabled")

# main.py remains the same and does not need to be changed.