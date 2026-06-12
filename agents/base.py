from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """Abstract base class for all Jarvis sub‑agents."""

    def __init__(self, context: Dict[str, Any]):
        self.context = context  # shared mutable state

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier used in the LLM JSON response."""
        ...

    @abstractmethod
    def handle(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the intent and return a JSON‑serialisable dict.
        Typical keys: ``speak``, ``result`` etc.
        """
        ...
