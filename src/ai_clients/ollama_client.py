# src/ai_clients/ollama_client.py

import requests
import json
from typing import Generator, List, Dict
from .base_client import BaseAIClient

class OllamaClient(BaseAIClient):
    """Client for local Ollama or OpenAI-compatible local models."""

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
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            data_str = decoded_line[len('data: '):].strip()
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except requests.RequestException as e:
            yield f"\n--- API请求错误 ---\n{e}"