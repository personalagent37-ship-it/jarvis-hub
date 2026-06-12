import smtplib, ssl
from email.message import EmailMessage
from .base import BaseAgent

class EmailAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "email"

    def handle(self, intent: str, params: dict) -> dict:
        if intent != "send":
            return {"speak": f"Unsupported email intent {intent}."}
        to = params.get("to")
        subject = params.get("subject", "")
        body = params.get("body", "")
        creds = self.context.get("smtp_credentials")
        if not creds:
            return {"speak": "SMTP credentials are missing."}
        msg = EmailMessage()
        msg["From"] = creds["address"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP_SSL(creds["host"], creds["port"], context=ssl.create_default_context()) as server:
                server.login(creds["address"], creds["password"])
                server.send_message(msg)
            return {"speak": f"Email sent to {to}."}
        except Exception as e:
            return {"speak": f"Failed to send email: {e}"}
