import logging
from .base import BaseAgent
from typing import Dict, Any

class AgentDispatcher:
    """Central hub that knows every registered sub‑agent."""

    def __init__(self, shared_context: Dict[str, Any]):
        self.context = shared_context
        self._registry: Dict[str, BaseAgent] = {}
        logging.getLogger(__name__).info("[Dispatcher] Initialized")

    def register(self, agent: BaseAgent) -> None:
        self._registry[agent.name] = agent
        logging.getLogger(__name__).info("[Dispatcher] Registered agent: %s", agent.name)

    def dispatch(self, agent_name: str, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name not in self._registry:
            raise ValueError(f"[Dispatcher] Unknown agent: {agent_name}")
        agent = self._registry[agent_name]
        logging.getLogger(__name__).debug("[Dispatcher] %s handling %s", agent_name, intent)
        return agent.handle(intent, params)
