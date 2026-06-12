import os
import requests
import json

class CarControl:
    """Control car via Tesla API (if token provided) or generic OBD‑II.
    
    The class checks environment configuration on init and provides a small
    set of high‑level actions that JARVIS can call.
    """
    def __init__(self):
        from config import CAR_CONTROL_ENABLED, TESLA_TOKEN
        self.enabled = CAR_CONTROL_ENABLED
        self.tesla_token = TESLA_TOKEN.strip()
        self.base_url = "https://owner-api.teslamotors.com/api/1/vehicles"

    def _request(self, method, endpoint, data=None):
        if not self.enabled or not self.tesla_token:
            return "Car control is disabled or missing token."
        headers = {"Authorization": f"Bearer {self.tesla_token}"}
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=10)
            else:
                resp = requests.post(url, headers=headers, json=data or {}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return f"Tesla API error: {e}"

    # ---------- High‑level actions ----------
    def lock(self):
        # Lock the first vehicle found
        info = self._request("GET", "/")
        if isinstance(info, dict) and info.get("response"):
            vehicle_id = info["response"][0]["id_s"]
            return self._request("POST", f"/{vehicle_id}/command/door_lock")
        return "Unable to locate vehicle for lock command."

    def unlock(self):
        info = self._request("GET", "/")
        if isinstance(info, dict) and info.get("response"):
            vehicle_id = info["response"][0]["id_s"]
            return self._request("POST", f"/{vehicle_id}/command/door_unlock")
        return "Unable to locate vehicle for unlock command."

    def start_charge(self):
        info = self._request("GET", "/")
        if isinstance(info, dict) and info.get("response"):
            vehicle_id = info["response"][0]["id_s"]
            return self._request("POST", f"/{vehicle_id}/command/charge_start")
        return "Unable to locate vehicle for start_charge."

    def stop_charge(self):
        info = self._request("GET", "/")
        if isinstance(info, dict) and info.get("response"):
            vehicle_id = info["response"][0]["id_s"]
            return self._request("POST", f"/{vehicle_id}/command/charge_stop")
        return "Unable to locate vehicle for stop_charge."

    def set_climate(self, temperature: float):
        info = self._request("GET", "/")
        if isinstance(info, dict) and info.get("response"):
            vehicle_id = info["response"][0]["id_s"]
            data = {"on": True, "temp": temperature}
            return self._request("POST", f"/{vehicle_id}/command/set_climate_state", data)
        return "Unable to locate vehicle for climate control."
