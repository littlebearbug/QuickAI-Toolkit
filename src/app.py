import customtkinter as ctk
import threading
import queue
import pyperclip

from src import prompts
from src.ai_clients import get_ai_client
from src.clipboard_handler import get_selected_text_auto
from src.hotkey_manager import start_listener
from src.settings_manager import SettingsManager
from src.ui.main_window import MainWindow

class QuickAIToolkit:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.withdraw()

        # --- State Management ---
        self.selected_text = ""
        self.response_queue = queue.Queue()
        self.is_task_running = False
        self.current_panel_view = "ai"

        # --- System Integration ---
        self.settings_manager = SettingsManager()
        self.ai_client = None
        self._create_ai_client()

        # --- UI Manager ---
        self.ui = MainWindow(root, self)

        # --- Start Background Services ---
        start_listener(self.on_hotkey_activate_auto, self.on_hotkey_activate_manual)
        self.process_queue()

    def _create_ai_client(self):
        provider_name = self.settings_manager.get("current_provider")
        provider_settings = self.settings_manager.get_current_provider_info()
        try:
            self.ai_client = get_ai_client(provider_name, provider_settings)
            print(f"AI client initialized for provider: {provider_name}")
        except ValueError as e:
            print(f"Error creating AI client: {e}")
            self.ai_client = None

    # --- Hotkey & Activation Logic ---
    def on_hotkey_activate_auto(self):
        self.root.after(0, self._activate_sequence, get_selected_text_auto, "auto")

    def on_hotkey_activate_manual(self):
        self.root.after(0, self._activate_sequence, pyperclip.paste, "manual")
        
    def _activate_sequence(self, text_getter, activation_mode: str):
        text = text_getter()
        if text and text.strip():
            self.selected_text = text
            self.ui.show(activation_mode=activation_mode)
        else:
            print("Activation failed: No text captured.")

    # --- AI Task Management ---
    def start_ai_task(self, action: str, **kwargs):
        if not self.ai_client:
            print("AI client not available. Check settings.")
            return
        if self.is_task_running:
            return
        
        self.is_task_running = True
        self.ui.display_loading() # Show panel and loading icon immediately
        
        messages = prompts.get_prompt_messages(action, self.selected_text, **kwargs)
        if messages:
            threading.Thread(target=self._run_ai_stream, args=(messages,), daemon=True).start()
        else:
            self.is_task_running = False # Reset if prompt generation fails
            self.ui.hide_panel()

    def _run_ai_stream(self, messages: list):
        try:
            stream_started = False
            for chunk in self.ai_client.stream_response(messages):
                if not stream_started:
                    self.response_queue.put("---START_STREAM---")
                    stream_started = True
                self.response_queue.put(chunk)
        finally:
            self.response_queue.put(None) # Sentinel value for stream end

    def process_queue(self):
        try:
            while not self.response_queue.empty():
                item = self.response_queue.get_nowait()
                if item == "---START_STREAM---":
                    self.ui.show_stream_start()
                elif item is None:
                    self.is_task_running = False
                else:
                    self.ui.append_stream_content(item)
        finally:
            self.root.after(100, self.process_queue)

    # --- Callbacks from UI ---
    def on_panel_hidden(self):
        """Callback executed when the UI panel is fully hidden."""
        self.is_task_running = False
        self.ui.clear_feedback_text()

    def show_settings_panel(self):
        if self.ui.is_panel_visible and self.current_panel_view == "ai":
            self.ui.switch_panel_view("settings")
        elif not self.ui.is_panel_visible:
            self.ui.switch_panel_view("settings")
            self.ui._show_panel_animated()

    def on_provider_change(self, provider_name: str):
        self.ui.populate_settings_ui()

    def save_settings(self):
        current_provider = self.ui.settings_widgets["provider_var"].get()
        new_settings = self.settings_manager.settings.copy()
        new_settings["current_provider"] = current_provider
        
        provider_settings = new_settings["providers"][current_provider]
        provider_settings["api_url"] = self.ui.settings_widgets["api_url_entry"].get()
        provider_settings["model_name"] = self.ui.settings_widgets["model_name_entry"].get()
        provider_settings["api_key"] = self.ui.settings_widgets["api_key_entry"].get()
        
        self.settings_manager.save_settings(new_settings)
        self._create_ai_client()
        self.ui.hide_panel()

    def on_language_select(self, lang_code: str):
        if hasattr(self.ui, "_translation_menu") and self.ui._translation_menu.winfo_exists():
            self.ui._translation_menu.destroy()
        self.start_ai_task("translate", target_language=lang_code)