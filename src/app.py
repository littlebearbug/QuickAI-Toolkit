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
        self.root.withdraw()

        self.selected_text = ""
        self.response_queue = queue.Queue()
        self.ai_client = AIClient(config.API_URL)
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # --- NEW: Setup for translation dropdown ---
        # A mapping from UI display name to the name used in prompts
        self.lang_map = {display: prompt_lang for display, prompt_lang in config.TRANSLATION_TARGETS}
        # A variable to control the dropdown's text
        self.translate_variable = ctk.StringVar(value="选择翻译语言...")
        
        self.popup_window = self._create_popup_window()

        start_listener(self.on_hotkey_activate_auto, self.on_hotkey_activate_manual)
        self.process_queue()

    # ... on_drag_start and on_drag_motion methods are unchanged ...
    def on_drag_start(self, event):
        self.drag_offset_x = self.popup_window.winfo_pointerx() - self.popup_window.winfo_x()
        self.drag_offset_y = self.popup_window.winfo_pointery() - self.popup_window.winfo_y()

    def on_drag_motion(self, event):
        x = self.popup_window.winfo_pointerx() - self.drag_offset_x
        y = self.popup_window.winfo_pointery() - self.drag_offset_y
        self.popup_window.geometry(f"+{x}+{y}")

    def _create_popup_window(self) -> ctk.CTkToplevel:
        popup = ctk.CTkToplevel(self.root)
        # ... (rest of popup setup is the same) ...
        popup.overrideredirect(True)
        popup.withdraw()
        popup.attributes("-topmost", True)
        popup.bind("<Escape>", self.hide_window)
        main_container = ctk.CTkFrame(popup, corner_radius=10, border_width=1)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        title_bar = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        title_bar.pack(side="top", fill="x", pady=(5, 0), padx=5)
        title_label = ctk.CTkLabel(title_bar, text="QuickAI Toolkit", font=ctk.CTkFont(weight="bold"))
        title_label.pack(side="left", padx=10)
        close_button = ctk.CTkButton(
            title_bar, text="✕", command=self.hide_window, width=28, height=28,
            text_color="white", fg_color="#333333", hover_color="#c42b1c"
        )
        close_button.pack(side="right")
        title_bar.bind("<ButtonPress-1>", self.on_drag_start)
        title_bar.bind("<B1-Motion>", self.on_drag_motion)
        title_label.bind("<ButtonPress-1>", self.on_drag_start)
        title_label.bind("<B1-Motion>", self.on_drag_motion)
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 5))

        # --- UI MODIFICATION START ---
        # Create a dropdown menu for translation
        translation_menu = ctk.CTkOptionMenu(
            button_frame,
            variable=self.translate_variable,
            values=[display for display, _ in config.TRANSLATION_TARGETS],
            command=self.on_language_select,
            width=140
        )
        translation_menu.pack(side="left", padx=5)

        # Other action buttons
        self.buttons = {
            "润色": self._create_button(button_frame, "润色", lambda: self.start_ai_task("polish_text")),
            "总结": self._create_button(button_frame, "总结", lambda: self.start_ai_task("summarize_points")),
        }
        # --- UI MODIFICATION END ---

        self.feedback_textbox = ctk.CTkTextbox(content_frame, wrap="word", state="disabled", font=("Segoe UI", 14), corner_radius=8)
        self.feedback_textbox.pack(fill="both", expand=True)
        return popup

    # --- NEW: Handler for the translation dropdown ---
    def on_language_select(self, selected_display_name: str):
        """Called when a language is selected from the dropdown menu."""
        prompt_language = self.lang_map.get(selected_display_name)
        if prompt_language:
            self.start_ai_task("translate", target_language=prompt_language)
        # Reset the dropdown text after a short delay for better UX
        self.root.after(500, lambda: self.translate_variable.set("选择翻译语言..."))

    # ... _create_button method is unchanged ...
    def _create_button(self, parent, text, command):
        button = ctk.CTkButton(parent, text=text, command=command)
        button.pack(side="left", fill="x", expand=True, padx=5)
        return button

    # ... on_hotkey_activate methods are unchanged ...
    def on_hotkey_activate_auto(self):
        self.root.after(0, self._activate_sequence, get_selected_text_auto)

    def on_hotkey_activate_manual(self):
        self.root.after(0, self._activate_sequence, pyperclip.paste)
        
    def _activate_sequence(self, text_getter):
        # ... (method logic is unchanged) ...
        text = text_getter()
        if text and text.strip():
            self.selected_text = text
            print(f"Captured text: '{self.selected_text[:100].strip()}...'")
            self.show_window()
        else:
            print("Activation failed: No text captured from clipboard or selection.")
    
    # ... show_window and hide_window methods are unchanged ...
    def show_window(self):
        self._clear_feedback()
        x, y = self.root.winfo_pointerxy()
        self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x - 50}+{y - 20}")
        self.popup_window.deiconify()
        self.popup_window.lift()
        self.popup_window.focus_force()

    def hide_window(self, event=None):
        self.popup_window.withdraw()

    # --- MODIFIED: start_ai_task now accepts kwargs ---
    def start_ai_task(self, action: str, **kwargs):
        self._set_ui_state(is_busy=True)
        self._clear_feedback()
        
        # Pass the kwargs (like target_language) to the prompt generator
        payload = prompts.get_prompt_payload(action, self.selected_text, config.MODEL_NAME, **kwargs)
        if payload:
            threading.Thread(target=self._run_ai_stream, args=(payload,), daemon=True).start()
        else:
            # If payload generation fails (e.g., bad action), re-enable UI
            self._set_ui_state(is_busy=False)

    # ... _run_ai_stream, process_queue, _set_ui_state, _clear_feedback are unchanged ...
    def _run_ai_stream(self, payload: dict):
        try:
            for chunk in self.ai_client.stream_response(payload):
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
        # Also disable/enable the dropdown menu
        state = "disabled" if is_busy else "normal"
        for widget in self.buttons.values():
            widget.configure(state=state)
        # Find the dropdown in the parent frame and configure its state
        button_frame = self.buttons["润色"].master
        for child in button_frame.winfo_children():
            if isinstance(child, ctk.CTkOptionMenu):
                child.configure(state=state)

    def _clear_feedback(self):
        self.feedback_textbox.configure(state="normal")
        self.feedback_textbox.delete("1.0", "end")
        self.feedback_textbox.configure(state="disabled")