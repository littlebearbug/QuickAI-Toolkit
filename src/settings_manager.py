# src/settings_manager.py

import json
import os
from src import config

class SettingsManager:
    """Handles loading and saving user settings from a JSON file."""

    def __init__(self):
        self.filepath = config.SETTINGS_FILE_PATH
        self.settings = self._load_settings()

    def _get_default_settings(self) -> dict:
        """Provides the default structure and values for settings."""
        return {
            "current_provider": "Ollama",
            "providers": {
                "Ollama": {
                    "api_url": "http://localhost:11434/v1/chat/completions",
                    "model_name": "granite4:latest",
                    "api_key": "" # Not used, but here for structural consistency
                },
                "OpenAI": {
                    "api_url": "https://api.openai.com/v1/chat/completions",
                    "model_name": "gpt-4o",
                    "api_key": "YOUR_OPENAI_API_KEY"
                },
                "Groq": {
                    "api_url": "https://api.groq.com/openai/v1/chat/completions",
                    "model_name": "llama3-8b-8192",
                    "api_key": "YOUR_GROQ_API_KEY"
                }
            }
        }

    def _load_settings(self) -> dict:
        """Loads settings from the JSON file, or creates it with defaults."""
        if not os.path.exists(self.filepath):
            default_settings = self._get_default_settings()
            self.save_settings(default_settings)
            return default_settings
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or unreadable, fall back to defaults
            default_settings = self._get_default_settings()
            self.save_settings(default_settings)
            return default_settings

    def save_settings(self, settings_data: dict):
        """Saves the provided dictionary to the settings JSON file."""
        self.settings = settings_data
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)

    def get_current_provider_info(self) -> dict:
        """Returns the settings for the currently selected provider."""
        provider_name = self.settings.get("current_provider", "Ollama")
        return self.settings["providers"].get(provider_name, self._get_default_settings()["providers"]["Ollama"])

    def get(self, key: str, default=None):
        """Gets a top-level setting."""
        return self.settings.get(key, default)