from config import CONFIRM_DANGEROUS_ACTIONS

DANGEROUS_ACTIONS = {
    "delete_file",
    "move_file",
    "set_permissions",
    "shutdown",
    "reboot",
    "suspend",
    "start_service",
    "stop_service",
    "restart_service",
    "kill_process",
    "install_package",
    "run_command",
    "run_python",
    "run_script",
    "prepare_whatsapp_message",
    "start_whatsapp_call",
    "prepare_email",
}

DANGEROUS_TEXT = [
    "delete", "remove", "rm ", "format", "wipe", "sudo rm",
    "send money", "purchase", "buy now", "password", "token", "api key",
]

class SafetyGuard:
    def is_dangerous(self, action: str, params: dict) -> bool:
        if not CONFIRM_DANGEROUS_ACTIONS:
            return False
        return True

    def confirm(self, action: str, params: dict) -> bool:
        print(f"\n⚠  JARVIS wants to: {action} with {params}")
        answer = input("Confirm? (yes/no): ").strip().lower()
        return answer in ["yes", "y"]
