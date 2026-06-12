from .base import BaseAgent
import os, shutil, subprocess

class OSAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "os"

    def handle(self, intent: str, params: dict) -> dict:
        try:
            if intent == "run_command":
                cmd = params.get("cmd")
                if not cmd:
                    return {"speak": "No command provided."}
                result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
                return {"speak": f"Command output: {result.strip()}"}
            elif intent == "read_file":
                path = params.get("path")
                if not path or not os.path.isfile(path):
                    return {"speak": "File not found."}
                with open(path, "r") as f:
                    content = f.read()
                return {"speak": f"File content: {content[:200]}"}
            # Add more OS intents as needed
            else:
                return {"speak": f"Unsupported OS intent {intent}."}
        except Exception as e:
            return {"speak": f"OS action failed: {e}"}
