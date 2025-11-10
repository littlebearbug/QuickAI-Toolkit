# src/ai_clients/base_client.py

from abc import ABC, abstractmethod
from typing import Generator, List, Dict

class BaseAIClient(ABC):
    """Abstract base class for all AI API clients."""
    
    @abstractmethod
    def stream_response(self, messages: List[Dict]) -> Generator[str, None, None]:
        """
        Sends a request to the LLM and yields content chunks from the stream.
        
        Args:
            messages: A list of message dictionaries, following OpenAI's format.

        Yields:
            String chunks of the AI's response.
        """
        pass