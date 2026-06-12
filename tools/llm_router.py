import os
import json
import requests
import subprocess
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL, ENABLE_OFFLINE_LLM, OFFLINE_MODEL_PATH

class LLMRouter:
    """Route LLM calls to OpenRouter (online) or a local Ollama model (offline).
    
    Usage:
        response = LLMRouter().chat(prompt, system_prompt=None)
    """
    def __init__(self, base_url=None, model=None):
        self.openrouter_key = OPENROUTER_API_KEY
        self.openrouter_model = model or OPENROUTER_MODEL
        self.openrouter_base = base_url or OPENROUTER_BASE_URL
        self.enable_offline = ENABLE_OFFLINE_LLM
        self.offline_model_path = OFFLINE_MODEL_PATH

    def _call_openrouter(self, messages):
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(self.openrouter_base, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"[LLM_ROUTER] OpenRouter error: {e}")
            return None

    def _call_offline(self, prompt, system_prompt=None):
        # Use Ollama CLI if available. The OFFLINE_MODEL_PATH can be a model name.
        model = self.offline_model_path or "llama3"
        try:
            # Build JSON for Ollama stdin
            payload = {"model": model, "prompt": prompt}
            if system_prompt:
                payload["system"] = system_prompt
            result = subprocess.run(
                ["ollama", "run", model],
                input=json.dumps(payload).encode(),
                capture_output=True,
                timeout=60,
            )
            if result.returncode != 0:
                print(f"[LLM_ROUTER] Ollama error: {result.stderr.decode()}")
                return None
            return result.stdout.decode().strip()
        except Exception as e:
            print(f"[LLM_ROUTER] Offline LLM error: {e}")
            return None

    def chat(self, user_message: str, system_prompt: str = None) -> str:
        """Return a response string from the appropriate LLM.
        If ONLINE fails or offline mode is forced, fallback accordingly.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        # Try online first unless offline forced
        if not self.enable_offline:
            resp = self._call_openrouter(messages)
            if resp:
                return resp
            # fall back to offline if online failed
            print("[LLM_ROUTER] Falling back to offline LLM")
        # Offline path
        return self._call_offline(user_message, system_prompt) or ""
