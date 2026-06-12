import os
from tools.llm_router import LLMRouter

class OfflineLLM:
    """High‑level wrapper for LLM calls that automatically selects online or offline.
    Used by the brain when `ENABLE_OFFLINE_LLM` is true or when the online service
    is unreachable.
    """
    def __init__(self):
        self.router = LLMRouter()
        self.system_prompt = None

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    def chat(self, user_message: str) -> str:
        """Return a response using the appropriate backend.
        If a system prompt is set it is passed to the router.
        """
        return self.router.chat(user_message, system_prompt=self.system_prompt)
