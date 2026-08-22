"""
LLM Client wrapper supporting Google Gemini, OpenAI, Groq, OpenRouter, and Mock providers using httpx.
"""
import os
import json
from typing import Optional, Dict, Any
import httpx


class LLMClient:
    """
    HTTP-based reusable LLM client for sending grounded prompts to API-based LLMs.
    Configurable via environment variables (LLM_PROVIDER, LLM_MODEL, LLM_API_KEY).
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        timeout: float = 60.0
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "google").lower()
        self.model = model or os.getenv("LLM_MODEL") or ("gemini-3.5-flash-lite" if self.provider == "google" else "gpt-4o-mini")
        
        # Check provider-specific keys if general LLM_API_KEY is not set
        self.api_key = (
            api_key or 
            os.getenv("LLM_API_KEY") or 
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("GROQ_API_KEY")
        )
        
        self.temperature = temperature
        self.timeout = timeout

        # Reuse single httpx client across requests
        self.http_client = httpx.Client(timeout=self.timeout)

        print(f"Initialized LLMClient (Provider: {self.provider}, Model: {self.model}, API Key Configured: {bool(self.api_key)})")

    def _call_google_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("LLM_API_KEY (or GEMINI_API_KEY) is missing for Google provider.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "response_mime_type": "application/json"
            }
        }

        resp = self.http_client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            raise ValueError(f"Malformed response structure from Google Gemini API: {data}") from err

    def _call_openai_compatible(self, endpoint_url: str, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError(f"LLM_API_KEY is missing for provider '{self.provider}'.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }

        resp = self.http_client.post(endpoint_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as err:
            raise ValueError(f"Malformed response structure from {self.provider} API: {data}") from err

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends system and user prompt to configured LLM provider and returns the raw response string.
        """
        if self.provider == "mock" or not self.api_key:
            if not self.api_key and self.provider != "mock":
                print(f"Warning: No API key found for provider '{self.provider}'. Operating in Mock/Fallback mode.")
            return json.dumps({
                "answer": "This is a fallback response. To enable live LLM generation, set a valid LLM_API_KEY in your .env file.",
                "limitations": "No active LLM API key detected in environment.",
                "source_ids": []
            })

        if self.provider in ["google", "gemini"]:
            return self._call_google_gemini(system_prompt, user_prompt)
        elif self.provider == "openai":
            return self._call_openai_compatible("https://api.openai.com/v1/chat/completions", system_prompt, user_prompt)
        elif self.provider == "groq":
            return self._call_openai_compatible("https://api.groq.com/openai/v1/chat/completions", system_prompt, user_prompt)
        elif self.provider == "openrouter":
            return self._call_openai_compatible("https://openrouter.ai/api/v1/chat/completions", system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: '{self.provider}'. Supported: google, openai, groq, openrouter, mock.")
