# src/ui/main_window.py

import customtkinter as ctk
from PIL import Image
import time
import pyperclip

from src import config

class MainWindow:
    """Manages the entire UI, including the window, widgets, and animations."""
    
    def __init__(self, root: ctk.CTk, app_logic):
        self.root = root
        self.app = app_logic  # Reference to the main application logic controller
        
        # --- UI State ---
        self.is_panel_visible = False
        self.is_animating = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # --- Load Resources ---
        self.icons = self._load_icons()

        # --- Create UI Elements ---
        self.popup = self._create_popup_window()
        
        self.combined_frame = ctk.CTkFrame(
            self.popup, 
            fg_color=config.TOOLBAR_BG_COLOR, 
            corner_radius=config.TOOLBAR_HEIGHT // 2 # Initial capsule shape
        )
        self.combined_frame.pack(fill="both", expand=True)
        self.combined_frame.pack_propagate(False)

        # Toolbar
        self.toolbar_frame = self._build_toolbar(self.combined_frame)
        self.toolbar_frame.pack(side="top", fill="x")

        # Result Panel (container for AI response and settings)
        self.result_panel = ctk.CTkFrame(self.combined_frame, fg_color="transparent")
        
        # AI Response View
        self.ai_response_frame = self._build_ai_response_view(self.result_panel)
        
        # Settings View
        self.settings_frame = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        self.settings_widgets = {}
        self._build_settings_ui(self.settings_frame)
        
    def _load_icons(self):
        icons = {}
        for name, path in config.ICON_PATHS.items():
            try:
                size = (24, 24) if name == "loading" else (18, 18)
                img = ctk.CTkImage(Image.open(path), size=size)
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
        popup.bind("<Escape>", lambda e: self.hide())
        popup.withdraw()
        return popup

    def _build_toolbar(self, parent) -> ctk.CTkFrame:
        toolbar = ctk.CTkFrame(parent, height=config.TOOLBAR_HEIGHT, fg_color="transparent")
        
        # Make the toolbar draggable
        toolbar.bind("<ButtonPress-1>", self._on_drag_start)
        toolbar.bind("<B1-Motion>", self._on_drag_motion)
        
        button_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_container.pack(expand=True)
        button_container.bind("<ButtonPress-1>", self._on_drag_start)
        button_container.bind("<B1-Motion>", self._on_drag_motion)
        
        self._create_icon_button(button_container, "translate", self._show_translation_menu)
        self._create_icon_button(button_container, "polish", lambda: self.app.start_ai_task("polish_text"))
        self._create_icon_button(button_container, "summarize", lambda: self.app.start_ai_task("summarize_points"))
        self._create_icon_button(button_container, "settings", self.app.show_settings_panel)
        self._create_icon_button(button_container, "close_app", self.hide)
        
        return toolbar

    def _build_ai_response_view(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(side="top", fill="x", padx=5, pady=(5, 0)) 
        
        copy_button = self._create_icon_button(
            header,
            "copy", 
            self._copy_results_to_clipboard, 
            hover_color=config.COPY_BUTTON_HOVER_COLOR
        )
        copy_button.pack(side="right")

        self.feedback_textbox = ctk.CTkTextbox(frame, wrap="word", state="disabled", fg_color="transparent", border_width=0)
        self.feedback_textbox.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 5))
        
        self.loading_label = ctk.CTkLabel(frame, text="", image=self.icons.get("loading"))

        footer = ctk.CTkFrame(frame, fg_color="transparent", height=40)
        footer.pack(side="bottom",pady=8, fill="x")
        
        close_panel_button = ctk.CTkButton(
            footer, text="", image=self.icons.get("close_app"), command=self.hide_panel,
            width=24, height=24, corner_radius=14, fg_color="transparent",
            hover_color=config.CLOSE_BUTTON_HOVER_COLOR
        )
        close_panel_button.pack(expand=True)
        
        return frame
        
    def _build_settings_ui(self, parent: ctk.CTkFrame):
        parent.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(parent, text="AI Provider").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        providers = list(self.app.settings_manager.get("providers").keys())
        self.settings_widgets["provider_var"] = ctk.StringVar(value=self.app.settings_manager.get("current_provider"))
        provider_menu = ctk.CTkOptionMenu(parent, variable=self.settings_widgets["provider_var"], values=providers, command=self.app.on_provider_change)
        provider_menu.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        
        ctk.CTkLabel(parent, text="API URL").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.settings_widgets["api_url_entry"] = ctk.CTkEntry(parent)
        self.settings_widgets["api_url_entry"].grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        
        ctk.CTkLabel(parent, text="Model Name").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.settings_widgets["model_name_entry"] = ctk.CTkEntry(parent)
        self.settings_widgets["model_name_entry"].grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        
        self.settings_widgets["api_key_label"] = ctk.CTkLabel(parent, text="API Key")
        self.settings_widgets["api_key_entry"] = ctk.CTkEntry(parent, show="*")
        
        save_button = ctk.CTkButton(parent, text="Save and Apply", command=self.app.save_settings)
        save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

    # --- Public Methods (API for the App Controller) ---

    def show(self, activation_mode: str):
        self.hide_panel(immediate=True)
        if activation_mode == "manual":
            w, h = self.popup.winfo_screenwidth(), self.popup.winfo_screenheight()
            x = (w // 2) - (config.WINDOW_WIDTH // 2)
            y = (h // 2) - (config.TOOLBAR_HEIGHT // 2)
        else:
            x, y = self.root.winfo_pointerxy()
            x -= 50; y -= 20
        
        self.popup.geometry(f"{config.WINDOW_WIDTH}x{config.TOOLBAR_HEIGHT}+{x}+{y}")
        self.popup.deiconify(); self.popup.lift(); self.popup.focus_force()

    def hide(self):
        self.popup.withdraw()

    def display_loading(self):
        """Show the panel with a loading indicator."""
        self.switch_panel_view("ai")
        self.clear_feedback_text()
        self.loading_label.place(relx=0.5, rely=0.4, anchor="center")
        self.feedback_textbox.pack_forget()
        self._show_panel_animated()
        
    def show_stream_start(self):
        """Hide loading and prepare textbox for streaming."""
        self.loading_label.place_forget()
        self.feedback_textbox.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 5))
        self.clear_feedback_text()
    
    def append_stream_content(self, text: str):
        self.feedback_textbox.configure(state="normal")
        self.feedback_textbox.insert("end", text)
        self.feedback_textbox.see("end")
        self.feedback_textbox.configure(state="disabled")

    def clear_feedback_text(self):
        self.feedback_textbox.configure(state="normal")
        self.feedback_textbox.delete("1.0", "end")
        self.feedback_textbox.configure(state="disabled")

    def hide_panel(self, immediate=False):
        if not self.is_panel_visible or self.is_animating:
            if immediate and self.combined_frame:
                self._finalize_hide()
            return
        
        if immediate:
            self._finalize_hide()
        else:
            self._animate_panel(
                start_height=config.TOOLBAR_HEIGHT + config.PANEL_MAX_HEIGHT,
                end_height=config.TOOLBAR_HEIGHT,
                on_finish=self._finalize_hide
            )
            
    def _finalize_hide(self):
        self.combined_frame.configure(height=config.TOOLBAR_HEIGHT, corner_radius=config.TOOLBAR_HEIGHT // 2)
        self.popup.geometry(f"{config.WINDOW_WIDTH}x{config.TOOLBAR_HEIGHT}")
        self.result_panel.pack_forget()
        self.app.on_panel_hidden() # Notify controller
        self.is_panel_visible = False
    
    def switch_panel_view(self, view: str):
        self.app.current_panel_view = view
        if view == "settings":
            self.ai_response_frame.pack_forget()
            self.settings_frame.pack(fill="both", expand=True)
            self.populate_settings_ui()
        else: # "ai"
            self.settings_frame.pack_forget()
            self.ai_response_frame.pack(fill="both", expand=True)

    def populate_settings_ui(self):
        provider_name = self.settings_widgets["provider_var"].get()
        provider_data = self.app.settings_manager.settings["providers"][provider_name]
        self.settings_widgets["api_url_entry"].delete(0, "end"); self.settings_widgets["api_url_entry"].insert(0, provider_data["api_url"])
        self.settings_widgets["model_name_entry"].delete(0, "end"); self.settings_widgets["model_name_entry"].insert(0, provider_data["model_name"])
        self.settings_widgets["api_key_entry"].delete(0, "end"); self.settings_widgets["api_key_entry"].insert(0, provider_data["api_key"])
        
        if provider_name == "Ollama":
            self.settings_widgets["api_key_label"].grid_forget(); self.settings_widgets["api_key_entry"].grid_forget()
        else:
            self.settings_widgets["api_key_label"].grid(row=3, column=0, padx=10, pady=8, sticky="w")
            self.settings_widgets["api_key_entry"].grid(row=3, column=1, padx=10, pady=8, sticky="ew")
            
    # --- Internal Helper Methods ---
    
    def _show_panel_animated(self):
        if self.is_panel_visible or self.is_animating:
            return
        self.result_panel.pack(side="top", fill="both", expand=True)
        def on_finish(): self.is_panel_visible = True
        self._animate_panel(config.TOOLBAR_HEIGHT, config.TOOLBAR_HEIGHT + config.PANEL_MAX_HEIGHT, on_finish)
    
    def _animate_panel(self, start_height, end_height, on_finish=None):
        if self.is_animating: return
        self.is_animating = True
        start_time = time.time()
        duration = config.ANIMATION_DURATION_MS / 1000.0

        def animation_step():
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            
            current_height = int(start_height + (end_height - start_height) * progress)
            self.combined_frame.configure(height=current_height)
            self.popup.geometry(f"{config.WINDOW_WIDTH}x{current_height}")

            # Dynamically adjust corner radius for smooth transition
            if end_height > start_height: # Expanding
                radius = int( (config.TOOLBAR_HEIGHT // 2) - ( (config.TOOLBAR_HEIGHT // 2) - config.CORNER_RADIUS) * progress )
            else: # Collapsing
                radius = int( config.CORNER_RADIUS + ( (config.TOOLBAR_HEIGHT // 2) - config.CORNER_RADIUS) * progress )
            self.combined_frame.configure(corner_radius=radius)

            if progress < 1.0:
                self.root.after(5, animation_step)
            else:
                self.is_animating = False
                if on_finish:
                    on_finish()
        animation_step()

    def _on_drag_start(self, event):
        self.drag_offset_x = self.popup.winfo_pointerx() - self.popup.winfo_x()
        self.drag_offset_y = self.popup.winfo_pointery() - self.popup.winfo_y()

    def _on_drag_motion(self, event):
        x = self.popup.winfo_pointerx() - self.drag_offset_x
        y = self.popup.winfo_pointery() - self.drag_offset_y
        self.popup.geometry(f"+{x}+{y}")

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
        x, y = translate_button.winfo_rootx(), translate_button.winfo_rooty() + translate_button.winfo_height() + 5
        
        menu = ctk.CTkToplevel(self.root)
        menu.overrideredirect(True); menu.attributes("-topmost", True); menu.geometry(f"+{x}+{y}")
        self._translation_menu = menu
        
        menu.bind("<FocusOut>", lambda e: menu.destroy())
        menu_frame = ctk.CTkFrame(menu, corner_radius=8); menu_frame.pack(padx=2, pady=2)
        for display, lang_code in config.TRANSLATION_TARGETS:
            lang_button = ctk.CTkButton(
                menu_frame, text=display, fg_color="transparent", anchor="w", text_color=config.TRANSLATION_BUTTON_COLOR,
                command=lambda lc=lang_code: self.app.on_language_select(lc)
            )
            lang_button.pack(fill="x", padx=5, pady=2)
        menu.focus_set()

    def _copy_results_to_clipboard(self):
        content = self.feedback_textbox.get("1.0", "end-1c")
        if content:
            pyperclip.copy(content)