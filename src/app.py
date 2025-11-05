# src/app.py

import customtkinter as ctk
import threading
import queue
from src import config, prompts
from src.ai_client import AIClient
from src.clipboard_handler import get_selected_text_auto
from src.hotkey_manager import start_listener
import pyperclip

class QuickAIToolkit:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.withdraw()  # Hide the main window
        
        self.selected_text = ""
        self.response_queue = queue.Queue()
        self.ai_client = AIClient(config.API_URL)
        
        self.popup_window = self._create_popup_window()
        
        start_listener(self.on_hotkey_activate_auto, self.on_hotkey_activate_manual)
        self.process_queue()

    def _create_popup_window(self) -> ctk.CTkToplevel:
        popup = ctk.CTkToplevel(self.root)
        popup.overrideredirect(True)
        popup.withdraw()
        popup.attributes("-topmost", True)
        
        popup.bind("<Escape>", self.hide_window)
        popup.bind("<FocusOut>", self.hide_window)

        main_frame = ctk.CTkFrame(popup, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=5)

        self.buttons = {
            "翻译成中文": self._create_button(button_frame, "翻译", lambda: self.start_ai_task("translate_chinese")),
            "润色优化": self._create_button(button_frame, "润色", lambda: self.start_ai_task("polish_text")),
            "总结要点": self._create_button(button_frame, "总结", lambda: self.start_ai_task("summarize_points")),
        }

        self.feedback_textbox = ctk.CTkTextbox(main_frame, wrap="word", state="disabled", font=("Segoe UI", 14), corner_radius=8)
        self.feedback_textbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        return popup

    def _create_button(self, parent, text, command):
        button = ctk.CTkButton(parent, text=text, command=command)
        button.pack(side="left", fill="x", expand=True, padx=5)
        return button

    def on_hotkey_activate_auto(self):
        self.root.after(0, self._activate_sequence, get_selected_text_auto)

    def on_hotkey_activate_manual(self):
        self.root.after(0, self._activate_sequence, pyperclip.paste)
        
    def _activate_sequence(self, text_getter):
        text = text_getter()
        if text and text.strip():
            self.selected_text = text
            print(f"Captured text: '{self.selected_text[:100].strip()}...'")
            self.show_window()
        else:
            print("Activation failed: No text captured from clipboard or selection.")
            
    def show_window(self):
        self._clear_feedback()
        x, y = self.root.winfo_pointerxy()
        self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x-50}+{y-20}")
        self.popup_window.deiconify()
        self.popup_window.focus_force()

    def hide_window(self, event=None):
        self.popup_window.withdraw()

    def start_ai_task(self, action: str):
        self._set_ui_state(is_busy=True)
        self._clear_feedback()
        
        payload = prompts.get_prompt_payload(action, self.selected_text, config.MODEL_NAME)
        if payload:
            threading.Thread(target=self._run_ai_stream, args=(payload,), daemon=True).start()

    def _run_ai_stream(self, payload: dict):
        try:
            for chunk in self.ai_client.stream_response(payload):
                self.response_queue.put(chunk)
        finally:
            self.response_queue.put(None) # Sentinel value to signal completion

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
            self.root.after(100, self.process_queue) # Poll the queue every 100ms
    
    def _set_ui_state(self, is_busy: bool):
        state = "disabled" if is_busy else "normal"
        for button in self.buttons.values():
            button.configure(state=state)

    def _clear_feedback(self):
        self.feedback_textbox.configure(state="normal")
        self.feedback_textbox.delete("1.0", "end")
        self.feedback_textbox.configure(state="disabled")