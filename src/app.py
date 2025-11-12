import customtkinter as ctk
import threading
import queue
import time
from PIL import Image
import pyperclip

from src import config, prompts
from src.ai_clients import get_ai_client
from src.clipboard_handler import get_selected_text_auto
from src.hotkey_manager import start_listener
from src.settings_manager import SettingsManager

class QuickAIToolkit:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.withdraw()

        # --- State Management ---
        self.selected_text = ""
        self.response_queue = queue.Queue()
        self.is_panel_visible = False
        self.is_animating = False
        self.is_task_running = False
        self.current_panel_view = "ai"
        
        ### --- NEW: Dragging State --- ###
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # --- System Integration ---
        self.settings_manager = SettingsManager()
        self.ai_client = None
        self._create_ai_client()

        # --- UI Elements ---
        self.popup_window = self._create_popup_window()
        self.combined_frame = None
        self.toolbar_frame = None
        
        self.result_panel = None
        self.ai_response_frame = None
        self.settings_frame = None
        
        self.feedback_textbox = None
        self.icons = self._load_icons()
        self.settings_widgets = {}

        self._build_ui()
        start_listener(self.on_hotkey_activate_auto, self.on_hotkey_activate_manual)
        self.process_queue()
    
    ### --- NEW: Dragging Methods --- ###
    def on_drag_start(self, event):
        """Captures the initial mouse position relative to the window."""
        self.drag_offset_x = self.popup_window.winfo_pointerx() - self.popup_window.winfo_x()
        self.drag_offset_y = self.popup_window.winfo_pointery() - self.popup_window.winfo_y()

    def on_drag_motion(self, event):
        """Moves the window based on the mouse's drag motion."""
        x = self.popup_window.winfo_pointerx() - self.drag_offset_x
        y = self.popup_window.winfo_pointery() - self.drag_offset_y
        self.popup_window.geometry(f"+{x}+{y}")

    # ... (Initialization methods _create_ai_client, _load_icons, _create_popup_window are unchanged) ...
    def _create_ai_client(self):
        provider_name = self.settings_manager.get("current_provider")
        provider_settings = self.settings_manager.get_current_provider_info()
        try:
            self.ai_client = get_ai_client(provider_name, provider_settings)
            print(f"AI client initialized for provider: {provider_name}")
        except ValueError as e:
            print(f"Error creating AI client: {e}")
            self.ai_client = None

    def _load_icons(self):
        icons = {}
        for name, path in config.ICON_PATHS.items():
            try:
                img = ctk.CTkImage(Image.open(path), size=(18, 18))
                icons[name] = img
            except FileNotFoundError:
                print(f"Warning: Icon not found at {path}")
                icons[name] = None
        return icons

    def _create_popup_window(self) -> ctk.CTkToplevel:
        popup = ctk.CTkToplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.attributes("-alpha", config.WINDOW_ALPHA)
        popup.config(bg=config.TRANSPARENT_COLOR)
        popup.attributes("-transparentcolor", config.TRANSPARENT_COLOR)
        popup.bind("<Escape>", lambda e: self.hide_window())
        popup.withdraw()
        return popup

    def _build_ui(self):
        self.combined_frame = ctk.CTkFrame(self.popup_window, fg_color=config.TOOLBAR_BG_COLOR, corner_radius=config.CORNER_RADIUS)
        self.combined_frame.pack(fill="both", expand=True)
        self.combined_frame.pack_propagate(False)

        # --- Toolbar ---
        self.toolbar_frame = ctk.CTkFrame(self.combined_frame, height=config.TOOLBAR_HEIGHT, fg_color="transparent")
        self.toolbar_frame.pack(side="top", fill="x")
        button_container = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        button_container.pack(expand=True)
        
        ### --- MODIFIED: Bind drag events to the toolbar --- ###
        self.toolbar_frame.bind("<ButtonPress-1>", self.on_drag_start)
        self.toolbar_frame.bind("<B1-Motion>", self.on_drag_motion)
        # Bind the container too, so empty spaces are draggable
        button_container.bind("<ButtonPress-1>", self.on_drag_start)
        button_container.bind("<B1-Motion>", self.on_drag_motion)
        
        self._create_icon_button(button_container, "translate", self._show_translation_menu)
        self._create_icon_button(button_container, "polish", lambda: self.start_ai_task("polish_text"))
        self._create_icon_button(button_container, "summarize", lambda: self.start_ai_task("summarize_points"))
        self._create_icon_button(button_container, "settings", self._show_settings_panel)
        self._create_icon_button(button_container, "close_app", self.hide_window)

        # ... (Rest of _build_ui and _build_settings_ui are unchanged) ...
        self.result_panel = ctk.CTkFrame(self.combined_frame, fg_color="transparent")
        self.result_panel.pack(side="top", fill="both", expand=True)

        self.ai_response_frame = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        panel_header = ctk.CTkFrame(self.ai_response_frame, fg_color="transparent")
        self._create_icon_button(panel_header, "copy", self._copy_results_to_clipboard, side="right", hover_color=config.COPY_BUTTON_HOVER_COLOR)
        self._create_icon_button(panel_header, "close_panel", self._hide_panel_animated, side="right", hover_color=config.CLOSE_BUTTON_HOVER_COLOR)
        panel_header.pack(side="top", fill="x", padx=5, pady=0)
        self.feedback_textbox = ctk.CTkTextbox(self.ai_response_frame, wrap="word", state="disabled", fg_color="transparent")
        self.feedback_textbox.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        self.settings_frame = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        self._build_settings_ui(self.settings_frame)
    
    def _build_settings_ui(self, parent: ctk.CTkFrame):
        parent.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(parent, text="AI Provider").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        providers = list(self.settings_manager.get("providers").keys())
        self.settings_widgets["provider_var"] = ctk.StringVar(value=self.settings_manager.get("current_provider"))
        provider_menu = ctk.CTkOptionMenu(parent, variable=self.settings_widgets["provider_var"], values=providers, command=self._on_provider_change)
        provider_menu.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(parent, text="API URL").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.settings_widgets["api_url_entry"] = ctk.CTkEntry(parent)
        self.settings_widgets["api_url_entry"].grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(parent, text="Model Name").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.settings_widgets["model_name_entry"] = ctk.CTkEntry(parent)
        self.settings_widgets["model_name_entry"].grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        self.settings_widgets["api_key_label"] = ctk.CTkLabel(parent, text="API Key")
        self.settings_widgets["api_key_entry"] = ctk.CTkEntry(parent, show="*")
        save_button = ctk.CTkButton(parent, text="Save and Close", command=self._save_settings)
        save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

    # ... (_create_icon_button, _show_translation_menu, _on_language_select are unchanged) ...
    def _create_icon_button(self, parent, icon_name, command, side="left", hover_color=None):
        button = ctk.CTkButton(
            parent, text="", image=self.icons.get(icon_name), command=command,
            width=config.BUTTON_SIZE, height=config.BUTTON_SIZE,
            corner_radius=config.BUTTON_SIZE // 2, fg_color="transparent",
            hover_color=hover_color or ctk.ThemeManager.theme["CTkButton"]["hover_color"]
        )
        button.pack(side=side, padx=6, pady=(8, 8))
        return button

    def _show_translation_menu(self):
        if hasattr(self, "_translation_menu") and self._translation_menu.winfo_exists():
            self._translation_menu.destroy()
            return
        translate_button = self.toolbar_frame.winfo_children()[0].winfo_children()[0]
        x = translate_button.winfo_rootx()
        y = translate_button.winfo_rooty() + translate_button.winfo_height() + 5
        menu = ctk.CTkToplevel(self.root)
        menu.overrideredirect(True); menu.attributes("-topmost", True); menu.geometry(f"+{x}+{y}")
        self._translation_menu = menu
        menu.bind("<FocusOut>", lambda e: menu.destroy())
        menu_frame = ctk.CTkFrame(menu, corner_radius=8); menu_frame.pack(padx=2, pady=2)
        for display, lang_code in config.TRANSLATION_TARGETS:
            lang_button = ctk.CTkButton(
                menu_frame, text=display, fg_color="transparent", anchor="w",text_color=config.TRANSLATION_BUTTON_COLOR,
                command=lambda lc=lang_code: self._on_language_select(lc)
            )
            lang_button.pack(fill="x", padx=5, pady=2)
        menu.focus_set()

    def _on_language_select(self, lang_code: str):
        if hasattr(self, "_translation_menu") and self._translation_menu.winfo_exists():
            self._translation_menu.destroy()
        self.start_ai_task("translate", target_language=lang_code)

    ### --- MODIFIED: Activation Logic --- ###
    def on_hotkey_activate_auto(self):
        # Pass "auto" to distinguish the activation method
        self.root.after(0, self._activate_sequence, get_selected_text_auto, "auto")

    def on_hotkey_activate_manual(self):
        # Pass "manual" to distinguish the activation method
        self.root.after(0, self._activate_sequence, pyperclip.paste, "manual")
        
    def _activate_sequence(self, text_getter, activation_mode: str):
        text = text_getter()
        if text and text.strip():
            self.selected_text = text
            # Pass the mode to the show_window method
            self.show_window(activation_mode=activation_mode)
        else:
            print("Activation failed: No text captured.")

    ### --- MODIFIED: Window & Panel Management --- ###
    def show_window(self, activation_mode: str):
        self._hide_panel_animated(immediate=True)

        if activation_mode == "manual":
            # Center the window on the screen for manual activation
            screen_width = self.popup_window.winfo_screenwidth()
            screen_height = self.popup_window.winfo_screenheight()
            win_width = config.WINDOW_WIDTH
            win_height = config.TOOLBAR_HEIGHT # Initial height
            x = (screen_width // 2) - (win_width // 2)
            y = (screen_height // 2) - (win_height // 2)
        else: # "auto" or default mode
            # Position the window near the mouse cursor
            x, y = self.root.winfo_pointerxy()
            x -= 50
            y -= 20
        
        initial_height = config.TOOLBAR_HEIGHT
        self.combined_frame.configure(height=initial_height)
        self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{initial_height}+{x}+{y}")
        
        self.popup_window.deiconify()
        self.popup_window.lift()
        self.popup_window.focus_force()

    # ... (The rest of the file: _switch_panel_view, _populate_settings_ui, _on_provider_change,
    # _save_settings, _show_settings_panel, start_ai_task, _run_ai_stream, animation methods, etc.
    # are all unchanged from the previous version and can remain as they are.)

    def _switch_panel_view(self, view: str):
        if view == "settings":
            self.ai_response_frame.pack_forget()
            self.settings_frame.pack(fill="both", expand=True)
            self._populate_settings_ui()
        else: # "ai"
            self.settings_frame.pack_forget()
            self.ai_response_frame.pack(fill="both", expand=True)
        self.current_panel_view = view
    
    def _populate_settings_ui(self):
        provider_name = self.settings_widgets["provider_var"].get()
        provider_data = self.settings_manager.settings["providers"][provider_name]
        self.settings_widgets["api_url_entry"].delete(0, "end"); self.settings_widgets["api_url_entry"].insert(0, provider_data["api_url"])
        self.settings_widgets["model_name_entry"].delete(0, "end"); self.settings_widgets["model_name_entry"].insert(0, provider_data["model_name"])
        self.settings_widgets["api_key_entry"].delete(0, "end"); self.settings_widgets["api_key_entry"].insert(0, provider_data["api_key"])
        if provider_name == "Ollama":
            self.settings_widgets["api_key_label"].grid_forget(); self.settings_widgets["api_key_entry"].grid_forget()
        else:
            self.settings_widgets["api_key_label"].grid(row=3, column=0, padx=10, pady=8, sticky="w")
            self.settings_widgets["api_key_entry"].grid(row=3, column=1, padx=10, pady=8, sticky="ew")

    def _on_provider_change(self, provider_name: str): self._populate_settings_ui()
    def _save_settings(self):
        current_provider = self.settings_widgets["provider_var"].get()
        new_settings = self.settings_manager.settings.copy()
        new_settings["current_provider"] = current_provider
        new_settings["providers"][current_provider]["api_url"] = self.settings_widgets["api_url_entry"].get()
        new_settings["providers"][current_provider]["model_name"] = self.settings_widgets["model_name_entry"].get()
        new_settings["providers"][current_provider]["api_key"] = self.settings_widgets["api_key_entry"].get()
        self.settings_manager.save_settings(new_settings); self._create_ai_client(); self._hide_panel_animated()

    def _show_settings_panel(self):
        if self.is_panel_visible and self.current_panel_view == "ai": self._switch_panel_view("settings")
        elif not self.is_panel_visible: self._switch_panel_view("settings"); self._show_panel_animated()
    
    def start_ai_task(self, action: str, **kwargs):
        if not self.ai_client: print("AI client not available. Check settings."); return
        if self.is_task_running: return
        self.is_task_running = True; self._switch_panel_view("ai"); self._hide_panel_animated(immediate=True); self._clear_feedback()
        messages = prompts.get_prompt_messages(action, self.selected_text, **kwargs)
        if messages: threading.Thread(target=self._run_ai_stream, args=(messages,), daemon=True).start()
        else: self.is_task_running = False
    
    def hide_window(self): self.popup_window.withdraw()
    def _animate_panel(self, start_height, end_height, on_finish=None):
        if self.is_animating: return
        self.is_animating = True; start_time = time.time(); duration = config.ANIMATION_DURATION_MS / 1000.0
        def animation_step():
            elapsed = time.time() - start_time; progress = min(elapsed / duration, 1.0)
            current_height = int(start_height + (end_height - start_height) * progress)
            self.combined_frame.configure(height=current_height)
            self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{current_height}")
            if progress < 1.0: self.root.after(5, animation_step)
            else: self.is_animating = False; on_finish() if on_finish else None
        animation_step()

    def _show_panel_animated(self):
        if self.is_panel_visible or self.is_animating: return
        def on_finish(): self.is_panel_visible = True
        self._animate_panel(config.TOOLBAR_HEIGHT, config.TOOLBAR_HEIGHT + config.PANEL_MAX_HEIGHT, on_finish)

    def _hide_panel_animated(self, immediate=False):
        if not self.is_panel_visible or self.is_animating:
            if immediate and self.combined_frame:
                self.combined_frame.configure(height=config.TOOLBAR_HEIGHT); self.popup_window.geometry(f"{config.WINDOW_WIDTH}x{config.TOOLBAR_HEIGHT}")
                self._clear_feedback(); self.is_panel_visible = False; self.is_task_running = False
            return
        def on_finish(): self.is_panel_visible = False; self.is_task_running = False; self._clear_feedback()
        self._animate_panel(config.TOOLBAR_HEIGHT + config.PANEL_MAX_HEIGHT, config.TOOLBAR_HEIGHT, on_finish)

    def _run_ai_stream(self, messages: list):
        try:
            stream_started = False
            for chunk in self.ai_client.stream_response(messages):
                if not stream_started: self.response_queue.put("---START_STREAM---"); stream_started = True
                self.response_queue.put(chunk)
        finally: self.response_queue.put(None)

    def process_queue(self):
        try:
            while not self.response_queue.empty():
                item = self.response_queue.get_nowait()
                if item == "---START_STREAM---": self._show_panel_animated()
                elif item is None: self.is_task_running = False
                else:
                    self.feedback_textbox.configure(state="normal"); self.feedback_textbox.insert("end", item)
                    self.feedback_textbox.see("end"); self.feedback_textbox.configure(state="disabled")
        finally: self.root.after(100, self.process_queue)
    
    def _clear_feedback(self):
        if self.feedback_textbox: self.feedback_textbox.configure(state="normal"); self.feedback_textbox.delete("1.0", "end"); self.feedback_textbox.configure(state="disabled")

    def _copy_results_to_clipboard(self):
        if self.feedback_textbox:
            content = self.feedback_textbox.get("1.0", "end-1c")
            if content: pyperclip.copy(content)