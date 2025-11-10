# src/ai_clients/__init__.py

from .base_client import BaseAIClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from typing import Type

# Mapping provider names to their client classes
CLIENT_MAP: dict[str, Type[BaseAIClient]] = {
    "Ollama": OllamaClient,
    "OpenAI": OpenAIClient,
    "Groq": OpenAIClient, # Groq uses an OpenAI-compatible API
}

def get_ai_client(provider_name: str, provider_settings: dict) -> BaseAIClient:
    """
    Factory function to get an instance of the appropriate AI client.
    
    Args:
        provider_name: The name of the AI provider (e.g., "Ollama", "OpenAI").
        provider_settings: A dictionary containing 'api_url', 'model_name', 'api_key'.
        
    Returns:
        An instance of a class that inherits from BaseAIClient.
    """
    client_class = CLIENT_MAP.get(provider_name)
    if not client_class:
        raise ValueError(f"Unknown AI provider: {provider_name}")
        
    return client_class(**provider_settings)