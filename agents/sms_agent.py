from .base import BaseAgent
try:
    from twilio.rest import Client
except Exception:
    Client = None  # Twilio library unavailable, will be disabled

class SmsAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "sms"

    def handle(self, intent: str, params: dict) -> dict:
        if intent != "send":
            return {"speak": f"Unsupported SMS intent {intent}."}
        if Client is None:
            return {"speak": "Twilio library not installed."}
        to = params.get("to")
        body = params.get("body", "")
        client = self.context.get("twilio_client")
        if not client:
            return {"speak": "Twilio credentials are missing."}
        try:
            client.messages.create(to=to, from_=self.context.get("twilio_number"), body=body)
            return {"speak": f"SMS sent to {to}."}
        except Exception as e:
            return {"speak": f"SMS failed: {e}"}
