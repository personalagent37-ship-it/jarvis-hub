import re

class PIIFilter:
    def __init__(self):
        # Email pattern
        self.email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        # Phone pattern (basic matching for 10-14 digit numbers with optional +, -, spaces)
        self.phone_pattern = re.compile(r'(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}')

    def redact_text(self, text: str) -> str:
        """Replaces PII in a string with redacted placeholders."""
        if not isinstance(text, str):
            return text
        
        redacted = self.email_pattern.sub('[EMAIL_REDACTED]', text)
        redacted = self.phone_pattern.sub('[PHONE_REDACTED]', redacted)
        return redacted

    def redact_messages(self, messages: list) -> list:
        """Redacts PII from a list of LLM message dictionaries before they are sent externally."""
        redacted_messages = []
        for msg in messages:
            new_msg = dict(msg)
            if isinstance(new_msg.get("content"), str):
                new_msg["content"] = self.redact_text(new_msg["content"])
            elif isinstance(new_msg.get("content"), list):
                # Handle multimodal content (e.g. vision context)
                new_content = []
                for item in new_msg["content"]:
                    new_item = dict(item)
                    if new_item.get("type") == "text" and isinstance(new_item.get("text"), str):
                        new_item["text"] = self.redact_text(new_item["text"])
                    new_content.append(new_item)
                new_msg["content"] = new_content
            redacted_messages.append(new_msg)
        return redacted_messages

# Global instance for easy importing
pii_filter = PIIFilter()
