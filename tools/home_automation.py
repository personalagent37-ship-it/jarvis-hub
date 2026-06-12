import os
import requests
import json

class HomeAutomation:
    """Simple wrapper for Home Assistant REST API.
    Requires HA_URL and HA_TOKEN in config.py.
    """
    def __init__(self):
        from config import HA_URL, HA_TOKEN, HOME_AUTOMATION_ENABLED
        self.enabled = HOME_AUTOMATION_ENABLED
        self.base_url = HA_URL.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        }

    def _call_service(self, domain: str, service: str, entity_id: str, data: dict = None):
        if not self.enabled:
            return "Home automation is disabled."
        url = f"{self.base_url}/api/services/{domain}/{service}"
        payload = {"entity_id": entity_id}
        if data:
            payload.update(data)
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            return f"Executed {domain}.{service} on {entity_id}."
        except Exception as e:
            return f"Home automation error: {e}"

    def turn_on(self, entity_id: str):
        return self._call_service("light", "turn_on", entity_id)

    def turn_off(self, entity_id: str):
        return self._call_service("light", "turn_off", entity_id)

    def set_brightness(self, entity_id: str, brightness: int):
        return self._call_service("light", "turn_on", entity_id, {"brightness": brightness})

    def set_temperature(self, entity_id: str, temperature: float):
        return self._call_service("climate", "set_temperature", entity_id, {"temperature": temperature})
