# src/ai_client.py

import requests
import json
from typing import Generator

class AIClient:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def stream_response(self, payload: dict) -> Generator[str, None, None]:
        """
        Sends a request to the LLM and yields content chunks from the stream.
        """
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
                                # Ignore malformed data chunks
                                continue
        except requests.RequestException as e:
            yield f"\n--- API请求错误 ---\n{e}"