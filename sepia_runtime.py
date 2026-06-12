import json
import os
import re
from datetime import datetime

from config import SEPIA_COMMANDS_FILE, USE_SEPIA_RUNTIME, USER_NAME


class SepiaRuntime:
    """Small SEPIA-inspired runtime for local intent and service routing."""

    def __init__(self, commands_file: str = SEPIA_COMMANDS_FILE):
        self.enabled = USE_SEPIA_RUNTIME
        self.commands_file = commands_file
        self.custom_commands = self._load_custom_commands()
        state = "enabled" if self.enabled else "disabled"
        print(f"[SEPIA] Local runtime {state}.")

    def process(self, command: str, context: list = None, memory=None) -> dict | None:
        if not self.enabled:
            return None

        text = self._normalize(command)
        if not text:
            return None

        custom = self._match_custom_command(text)
        if custom:
            return custom

        result = self._memory_intent(text, memory)
        if result:
            return result

        result = self._conversation_intent(text)
        if result:
            return result

        result = self._communication_intent(text)
        if result:
            return result

        result = self._file_intent(text)
        if result:
            return result

        result = self._local_service_intent(text)
        if result:
            return result

        result = self._web_intent(text)
        if result:
            return result

        return None

    def _communication_intent(self, text: str) -> dict | None:
        if "mail" in text or "email" in text or "gmail" in text:
            if re.search(r"\b(?:open|check|show)\s+(?:my\s+)?(?:mail|email|gmail)\b", text):
                return {
                    "speak": "Opening your mail now.",
                    "action": "open_mail",
                    "params": {},
                }
            search_match = re.search(r"(?:search|find)\s+(?:my\s+)?(?:mail|email|gmail)\s+(?:for\s+)?(.+)", text)
            if search_match:
                query = search_match.group(1).strip()
                return {
                    "speak": f"Searching your mail for {query}.",
                    "action": "search_mail",
                    "params": {"query": query},
                }
            email_match = re.search(r"(?:email|mail)\s+(.+?)\s+(?:saying|that|message)\s+(.+)", text)
            if email_match:
                recipient = email_match.group(1).strip()
                body = email_match.group(2).strip()
                return {
                    "speak": f"Preparing an email draft for {recipient}.",
                    "action": "prepare_email",
                    "params": {"to": recipient, "subject": "", "body": body},
                }

        if "whatsapp" in text or "whats app" in text:
            call_match = re.search(r"(?:call|voice call|video call)\s+(?:to\s+)?(.+?)(?:\s+on\s+whats\s?app|\s+whats\s?app|$)", text)
            if call_match:
                contact = self._clean_contact(call_match.group(1))
                return {
                    "speak": f"Preparing a WhatsApp call with {contact}.",
                    "action": "start_whatsapp_call",
                    "params": {"contact": contact, "video": "video" in text},
                }

            message_match = re.search(
                r"(?:message|send message|text)\s+(?:to\s+)?(.+?)(?:\s+on\s+whats\s?app|\s+whats\s?app)?(?:\s+(?:saying|that|message|hi|hello)\s*(.*))?$",
                text,
            )
            if not message_match:
                message_match = re.search(r"open\s+whats\s?app\s+and\s+message\s+(?:to\s+)?(.+)", text)
            if message_match:
                contact = self._clean_contact(message_match.group(1))
                message = ""
                if len(message_match.groups()) >= 2 and message_match.group(2):
                    message = message_match.group(2).strip()
                if not message and (" hi" in text or text.endswith(" hi")):
                    message = "Hi"
                return {
                    "speak": f"Preparing WhatsApp for {contact}.",
                    "action": "prepare_whatsapp_message",
                    "params": {"contact": contact, "message": message},
                }

            if re.search(r"\b(?:open|show)\s+whats\s?app\b", text):
                return {
                    "speak": "Opening WhatsApp now.",
                    "action": "browse_url",
                    "params": {"url": "https://web.whatsapp.com"},
                }

        return None

    def _clean_contact(self, text: str) -> str:
        text = re.sub(r"\b(on|whatsapp|whats|app|please|hi|hello|message|call|to)\b", " ", text)
        text = re.sub(r"\s+", " ", text).strip(" ,.")
        return text.title() if text else ""

    def _file_intent(self, text: str) -> dict | None:
        folders = {
            "desktop": "~/Desktop",
            "downloads": "~/Downloads",
            "download": "~/Downloads",
            "documents": "~/Documents",
            "document": "~/Documents",
            "home": "~",
            "pictures": "~/Pictures",
            "videos": "~/Videos",
            "music": "~/Music",
        }

        for name, path in folders.items():
            if re.search(rf"\b(?:open|show|list)\s+(?:my\s+)?{name}\b", text):
                return {
                    "speak": f"Opening your {name} folder now.",
                    "action": "open_app",
                    "params": {"app": path},
                }
            if re.search(rf"\b(?:what is in|list files in|show files in)\s+(?:my\s+)?{name}\b", text):
                return {
                    "speak": f"Listing files in your {name} folder.",
                    "action": "list_files",
                    "params": {"path": path},
                }

        search_match = re.search(r"(?:find|search for)\s+(?:file\s+)?(.+?)\s+(?:in|inside)\s+(desktop|downloads|documents|home)", text)
        if search_match:
            pattern = search_match.group(1).strip()
            folder = folders.get(search_match.group(2), "~")
            return {
                "speak": f"Searching for {pattern} now.",
                "action": "search_files",
                "params": {"pattern": pattern, "path": folder},
            }

        create_match = re.search(r"(?:create|make)\s+(?:a\s+)?folder\s+(?:called|named)?\s*([a-z0-9 _-]+)\s+(?:on|in)\s+(desktop|downloads|documents|home)", text)
        if create_match:
            folder_name = create_match.group(1).strip().replace(" ", "_")
            base = folders.get(create_match.group(2), "~")
            return {
                "speak": f"Creating the {folder_name} folder now.",
                "action": "create_folder",
                "params": {"path": os.path.join(base, folder_name)},
            }

        return None

    def _load_custom_commands(self) -> list:
        if not os.path.exists(self.commands_file):
            return []
        try:
            with open(self.commands_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception as error:
            print(f"[SEPIA] Could not load custom commands: {error}")
            return []

        if not isinstance(data, list):
            print("[SEPIA] Custom commands file must contain a list.")
            return []
        return [item for item in data if isinstance(item, dict)]

    def _match_custom_command(self, text: str) -> dict | None:
        for item in self.custom_commands:
            phrases = item.get("phrases", [])
            if isinstance(phrases, str):
                phrases = [phrases]
            if any(self._normalize(phrase) == text for phrase in phrases):
                speak = item.get("speak", "I found a matching custom command.")
                action = item.get("action")
                params = item.get("params", {})
                return {"speak": speak, "action": action, "params": params}
        return None

    def _memory_intent(self, text: str, memory) -> dict | None:
        if memory is None:
            return None

        remember_match = re.search(
            r"^(?:remember that\s+)?(?:my\s+)?([a-z0-9 _-]{2,40})\s+(?:is|equals|=)\s+(.+)$",
            text,
        )
        if remember_match and ("remember" in text or text.startswith("my ")):
            key = self._fact_key(remember_match.group(1))
            value = remember_match.group(2).strip()
            if key and value:
                memory.save_fact(key, value)
                return {
                    "speak": f"I will remember that your {key.replace('_', ' ')} is {value}.",
                    "action": None,
                    "params": {},
                }

        recall_match = re.search(
            r"^(?:what is|whats|tell me|do you remember)\s+(?:my\s+)?([a-z0-9 _-]{2,40})\??$",
            text,
        )
        if recall_match:
            key = self._fact_key(recall_match.group(1))
            value = memory.get_fact(key)
            if value:
                return {
                    "speak": f"Your {key.replace('_', ' ')} is {value}.",
                    "action": None,
                    "params": {},
                }

        return None

    def _conversation_intent(self, text: str) -> dict | None:
        if text in {"hi", "hello", "hey", "hey jarvis", "hello jarvis"}:
            return {
                "speak": f"Hello {USER_NAME}, I am ready for your command.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["can you hear me", "are you listening", "listen me"]):
            return {
                "speak": f"I hear you, {USER_NAME}. I am listening for your next instruction.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["what are you doing", "what you doing"]):
            return {
                "speak": "I am awake, watching for your instructions, and ready to work.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["your mood", "how is your mood", "mood today"]):
            return {
                "speak": "Steady and operational, Talha. I am ready to help you move.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["what time", "current time", "tell me time"]):
            now = datetime.now().strftime("%I:%M %p")
            return {
                "speak": f"It is currently {now}, {USER_NAME}.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["what date", "today date", "current date"]):
            today = datetime.now().strftime("%A, %B %d, %Y")
            return {
                "speak": f"Today is {today}.",
                "action": None,
                "params": {},
            }

        if any(phrase in text for phrase in ["what can you do", "your status", "jarvis status"]):
            return {
                "speak": "My SEPIA-style runtime is active with local intents, memory, web actions, system actions, and LLM fallback.",
                "action": None,
                "params": {},
            }

        return None

    def _local_service_intent(self, text: str) -> dict | None:
        app_match = re.search(r"^(?:open|launch|start)\s+([a-z0-9 ._-]+)$", text)
        if app_match:
            app = app_match.group(1).strip()
            if app in {"terminal", "the terminal"}:
                return {
                    "speak": "Opening the terminal for you now.",
                    "action": "open_terminal",
                    "params": {},
                }
            if "." not in app and app not in self._known_sites():
                return {
                    "speak": f"Opening {app} for you now.",
                    "action": "open_app",
                    "params": {"app": app},
                }

        service_map = [
            (["system info", "computer info", "device info"], "get_system_info", "Getting your system information now."),
            (["battery"], "get_battery_info", "Checking your battery information now."),
            (["network info", "wifi info", "internet info"], "get_network_info", "Checking your network information now."),
            (["running processes", "process list"], "get_processes", "Getting the running process list now."),
            (["screenshot", "take screenshot"], "take_screenshot", "Taking a screenshot now."),
            (["describe screen", "read screen"], "describe_screen", "Reading the visible screen content now."),
        ]
        for phrases, action, speak in service_map:
            if any(phrase in text for phrase in phrases):
                return {"speak": speak, "action": action, "params": {}}

        return None

    def _web_intent(self, text: str) -> dict | None:
        sites = self._known_sites()
        for name, url in sites.items():
            if re.search(rf"\b(?:open|go to|browse)\s+{re.escape(name)}\b", text):
                return {
                    "speak": f"Opening {name.title()} for you now.",
                    "action": "browse_url",
                    "params": {"url": url},
                }

        website_match = re.search(r"(?:open|go to|browse)\s+((?:https?://)?[a-z0-9.-]+\.[a-z]{2,})", text)
        if website_match:
            url = website_match.group(1)
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            return {
                "speak": f"Opening {url} in your browser now.",
                "action": "browse_url",
                "params": {"url": url},
            }

        search_match = re.search(
            r"(?:search\s+(?:google\s+)?(?:for\s+)?|google\s+(?:for\s+)?|look up\s+|find\s+)(.+)",
            text,
        )
        if search_match:
            query = search_match.group(1).strip()
            if query:
                return {
                    "speak": f"Searching Google for {query} now.",
                    "action": "search_web",
                    "params": {"query": query},
                }

        return None

    def _known_sites(self) -> dict:
        return {
            "youtube": "https://youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "whats app": "https://web.whatsapp.com",
            "google": "https://google.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "chatgpt": "https://chatgpt.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "linkedin": "https://linkedin.com",
            "amazon": "https://amazon.com",
            "flipkart": "https://flipkart.com",
            "netflix": "https://netflix.com",
        }

    def _normalize(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = re.sub(r"\b(jarvis|javis|jarves|javi)\b[:,]?\s*", "", text)
        text = re.sub(r"[^a-z0-9 ./_?=-]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _fact_key(self, text: str) -> str:
        text = re.sub(r"^(?:my|the)\s+", "", text.strip().lower())
        text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
        return text[:40]
