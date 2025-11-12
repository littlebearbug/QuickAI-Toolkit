# src/ai_clients/ollama_client.py

import requests
import json
from typing import Generator, List, Dict
from .base_client import BaseAIClient

class OllamaClient(BaseAIClient):
    """Client for native Ollama API."""

    def __init__(self, api_url: str, model_name: str, **kwargs):
        self.api_url = api_url
        self.model_name = model_name

    def stream_response(self, messages: List[Dict]) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }
        
        try:
            with requests.post(self.api_url, json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            # Ollama's native stream format is one JSON object per line
                            data = json.loads(line.decode('utf-8'))
                            
                            # Check for errors in the stream
                            if "error" in data:
                                yield f"\n--- OLLAMA API ERROR ---\n{data['error']}"
                                break

                            # The final summary object has 'done: true' and no 'message'
                            if data.get("done"):
                                break
                            
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            # Skip empty or malformed lines
                            continue
        except requests.RequestException as e:
            yield f"\n--- API请求错误 ---\n{e}"