#!/usr/bin/env python3
import argparse
import fcntl
import os
import re
import sys
import time
from difflib import SequenceMatcher

# New imports for extended capabilities
from tools.os_actions import OSActions
from tools.car_control import CarControl
from tools.home_automation import HomeAutomation
from config import UI_OVERLAY_ENABLED, CONFIRM_DANGEROUS_ACTIONS
from brain import JarvisBrain
from army import deploy_agent

HIGH_RISK_ACTIONS = {"delete_file", "shutdown", "reboot", "format", "wipe"}
from stt import SpeechToText
from tts import TextToSpeech
from vision import Vision
from memory import Memory
from safety import SafetyGuard
from wake_word import WakeWordDetector
from config import PORTAL_URL, POST_SPEECH_PAUSE
import tools.computer_use as computer
import tools.file_manager as files
import tools.browser as browser
import tools.code_runner as runner
import tools.system_info as sysinfo
import tools.system_control as sysctl

LOCK_FILE = "/tmp/jarvis_voice_assistant.lock"
_LOCK_HANDLE = None


def acquire_single_instance_lock() -> bool:
    global _LOCK_HANDLE
    _LOCK_HANDLE = open(LOCK_FILE, "w")
    try:
        fcntl.flock(_LOCK_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _LOCK_HANDLE.write(str(os.getpid()))
        _LOCK_HANDLE.flush()
        return True
    except BlockingIOError:
        print("JARVIS is already running. Use the wake word instead of starting another copy.")
        return False

class Jarvis:
    def __init__(self, voice_enabled: bool = False, wake_enabled: bool = False):
        print("=" * 50)
        print("  JARVIS — Starting up...")
        print("=" * 50)
        self.tts = TextToSpeech()
        self.stt = SpeechToText() if voice_enabled else None
        self.memory = Memory()
        # Initialise extended helpers
        self.os_actions = OSActions()
        self.car_control = CarControl()
        self.home_automation = HomeAutomation()
        # UI overlay – start if enabled
        self.overlay = None
        if UI_OVERLAY_ENABLED:
            from ui.overlay import start_overlay
            app, window = start_overlay()
            self.overlay = window
            # Run the Qt event loop in a background daemon thread
            import threading
            threading.Thread(target=app.exec, daemon=True).start()
        self.brain = JarvisBrain()
        self.vision = Vision()
        self.safety = SafetyGuard()
        self.wake = WakeWordDetector(keyword="jarvis") if wake_enabled else None
        self.last_spoken = ""
        self.sleeping = wake_enabled
        print("=" * 50)
        print("  All systems ready.")
        print("=" * 50)
        if PORTAL_URL:
            try:
                print(f"[PORTAL] Opening local portal at {PORTAL_URL}")
                browser.navigate(PORTAL_URL)
            except Exception as e:
                print(f"[PORTAL] Failed to open portal: {e}")

    def speak(self, text: str):
        self.last_spoken = text or ""
        self.tts.speak(text)
        # Push spoken text to UI overlay if present
        if getattr(self, "overlay", None):
            try:
                self.overlay.push_message(text)
            except Exception:
                pass
        time.sleep(POST_SPEECH_PAUSE)

    def calibrate_mic(self, params: dict) -> str:
        """
        Adjust microphone thresholds based on provided parameters and update config.py.
        Expected keys: stt_silence_threshold, stt_silence_seconds, wake_min_volume.
        """
        try:
            with open('config.py', 'r') as f:
                lines = f.readlines()
            with open('config.py', 'w') as f:
                for line in lines:
                    if line.startswith('STT_SILENCE_THRESHOLD') and 'stt_silence_threshold' in params:
                        f.write(f'ST T_SILENCE_THRESHOLD = {float(params["stt_silence_threshold"])}\n')
                    elif line.startswith('STT_SILENCE_SECONDS') and 'stt_silence_seconds' in params:
                        f.write(f'ST T_SILENCE_SECONDS = {float(params["stt_silence_seconds"])}\n')
                    elif line.startswith('WAKE_MIN_VOLUME') and 'wake_min_volume' in params:
                        f.write(f'WAKE_MIN_VOLUME = {float(params["wake_min_volume"])}\n')
                    else:
                        f.write(line)
            return "Microphone calibrated."
        except Exception as e:
            return f"Calibration failed: {e}"

    def confirm_action(self, action: str) -> bool:
        """Prompt user for confirmation of high‑risk actions."""
        self.speak(f"Are you sure you want to {action}, Talha?")
        if self.stt:
            resp = self.stt.listen_and_transcribe().lower()
        else:
            resp = input("Confirm action? ").strip().lower()
        return self.is_confirmation_yes(resp)

    def _normalize_voice_text(self, text: str) -> str:
        text = text.lower()
        replacements = {
            "tell her": "talha",
            "tell ha": "talha",
            "i k": "key",
            "a k": "api key",
            "ironman tile": "environment file",
            "entirely": "environment file",
            "on the right": "not authorized",
            "out authorized": "not authorized",
            "not on the right": "not authorized",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return re.sub(r"[^a-z0-9 ]+", "", text).strip()

    def is_echo(self, command: str) -> bool:
        if not self.last_spoken:
            return False
        heard = self._normalize_voice_text(command)
        spoken = self._normalize_voice_text(self.last_spoken)
        if not heard or not spoken:
            return False

        command_markers = [
            "message", "whatsapp", "whats app", "send", "open", "search",
            "click", "type", "write", "call", "farhan", "group",
        ]
        if any(marker in heard for marker in command_markers):
            if not any(marker in spoken for marker in command_markers):
                return False
            if len(set(heard.split()) - set(spoken.split())) >= 2:
                return False

        if heard in spoken or spoken in heard:
            return True
        heard_words = set(heard.split())
        spoken_words = set(spoken.split())
        if len(heard_words) >= 4 and spoken_words:
            overlap = len(heard_words & spoken_words) / len(heard_words)
            if overlap >= 0.45:
                return True
        echo_markers = [
            "api key",
            "valid key",
            "not authorized",
            "environment file",
            "listening for your command",
        ]
        if any(marker in heard and marker in spoken for marker in echo_markers):
            return True
        return SequenceMatcher(None, heard, spoken).ratio() > 0.62

    def execute_action(self, action: str, params: dict) -> str:
        if not action or action in ["null", "none", "None"]:
            return ""
        params = params or {}
        action_map = {
            # GUI Control
            "click":              lambda p: computer.click(**p),
            "type_text":          lambda p: computer.type_text(**p),
            "hotkey":             lambda p: computer.hotkey(**p),
            "scroll":             lambda p: computer.scroll(**p),
            "take_screenshot":    lambda p: computer.take_screenshot(),
            
            # Apps & Browser
            "open_app":           lambda p: self.os_actions.open_app(p.get('app')),
            "open_terminal":      lambda p: computer.open_terminal(),
            "browse_url":         lambda p: browser.navigate(**p),
            "search_web":         lambda p: browser.search_web(**p),
            "open_mail":          lambda p: browser.open_mail(),
            "search_mail":        lambda p: browser.search_mail(),
            "read_mail_page":     lambda p: browser.read_mail_page(),
            "prepare_email":      lambda p: browser.prepare_email(**p),
            "prepare_whatsapp_message": lambda p: browser.prepare_whatsapp_message(**p),
            "start_whatsapp_call": lambda p: browser.start_whatsapp_call(**p),
            
            # File Operations
            "read_file":          lambda p: self.os_actions.read_file(p.get('path')),
            "write_file":         lambda p: self.os_actions.write_file(p.get('path'), p.get('content')),
            "append_file":        lambda p: self.os_actions.append_file(p.get('path'), p.get('content')),
            "create_folder":      lambda p: self.os_actions.create_folder(p.get('path')),
            "delete_file":        lambda p: self.os_actions.delete_file(p.get('path')),
            "copy_file":          lambda p: self.os_actions.copy_file(p.get('source'), p.get('dest')),
            "move_file":          lambda p: self.os_actions.move_file(p.get('source'), p.get('dest')),
            "list_files":         lambda p: self.os_actions.list_files(p.get('path')),
            "search_files":       lambda p: self.os_actions.search_files(p.get('pattern'), p.get('path')),
            "get_file_info":      lambda p: self.os_actions.get_file_info(p.get('path')),
            "set_permissions":    lambda p: files.set_permissions(**p),
            
            # System Info
            "get_system_info":    lambda p: sysinfo.get_system_info(),
            "get_processes":      lambda p: sysinfo.get_running_processes(),
            "get_network_info":   lambda p: sysinfo.get_network_info(),
            "get_battery_info":   lambda p: sysinfo.get_battery_info(),
            "describe_screen":    lambda p: self.vision.get_screen_text(),
            
            # System Control
            "shutdown":           lambda p: sysctl.shutdown(**p),
            "reboot":             lambda p: sysctl.reboot(**p),
            "lock_screen":        lambda p: sysctl.lock_screen(),
            "suspend":            lambda p: sysctl.suspend(),
            "start_service":      lambda p: sysctl.start_service(**p),
            "stop_service":       lambda p: sysctl.stop_service(**p),
            "restart_service":    lambda p: sysctl.restart_service(**p),
            "kill_process":       lambda p: sysctl.kill_process(**p),
            
            # Code Execution
            "run_command":        lambda p: self.os_actions.run_command(p.get('command')),
            "run_python":         lambda p: runner.run_python(**p),
            "install_package":    lambda p: self.os_actions.install_package(p.get('package')),
            "list_packages":      lambda p: self.os_actions.list_packages(),
            "run_script":         lambda p: runner.run_script(**p),
            
            # Clipboard
            "get_clipboard":      lambda p: sysctl.get_clipboard(),
            "clear_clipboard":    lambda p: sysctl.clear_clipboard(),
            
            # Car Control
            "lock_car":           lambda p: self.car_control.lock(),
            "unlock_car":         lambda p: self.car_control.unlock(),
            "start_charge":       lambda p: self.car_control.start_charge(),
            "stop_charge":        lambda p: self.car_control.stop_charge(),
            "set_climate":        lambda p: self.car_control.set_climate(p.get('temperature')),
            
            # Home Automation
            "ha_turn_on":         lambda p: self.home_automation.turn_on(p.get('entity_id')),
            "ha_turn_off":        lambda p: self.home_automation.turn_off(p.get('entity_id')),
            "ha_set_brightness":  lambda p: self.home_automation.set_brightness(p.get('entity_id'), p.get('brightness')),
            "ha_set_temperature": lambda p: self.home_automation.set_temperature(p.get('entity_id'), p.get('temperature')),
            
            # Persistent Memory
            "save_fact":          lambda p: (self.memory.save_fact(p.get("key"), p.get("value")), f"Saved fact: {p.get('key')} = {p.get('value')}")[1],
            "get_fact":           lambda p: self.memory.get_fact(p.get("key")) or "I do not remember that.",
            
            # Vision
            "camera_snapshot":    lambda p: self.vision.get_camera_snapshot(),
            "calibrate_mic":     lambda p: self.calibrate_mic(p),
            
            # Jarvis Army Delegation
            "deploy_army":        lambda p: deploy_agent(p.get('agent'), p.get('task')),
        }
        handler = action_map.get(action)
        if not handler:
            print(f"[ACTION] Unknown: {action}")
            return ""



        try:
            result = handler(params)
            print(f"[ACTION] {action} completed: {str(result)[:80]}")
            return str(result)
        except Exception as e:
            print(f"[ACTION ERROR] {action}: {e}")
            return f"error: {e}"

    def is_confirmation_yes(self, text: str) -> bool:
        text = self._normalize_voice_text(text or "")
        no_words = ["no", "dont", "do not", "cancel", "stop", "not now"]
        if any(word in text for word in no_words):
            return False
        yes_words = [
            "yes", "yeah", "yep", "do it", "go ahead", "continue", "confirm",
            "approved", "okay", "ok", "haan", "han", "ha", "kar do", "kardo",
            "chalo", "theek hai", "proceed",
        ]
        return any(word in text for word in yes_words)

    def handle_command(self, command: str):
        if not command or len(command.strip()) < 2:
            return
        command = self.clean_command(command)
        if not command:
            return
        lowered = command.lower()
        if self.is_noise_command(lowered):
            print("[VOICE] Ignored noisy transcription.")
            return
        if self.should_sleep(lowered):
            self.sleeping = True
            self.speak("Sleeping now, Talha.")
            return
        if self.sleeping:
            if self.should_wake(lowered):
                self.sleeping = False
                command = self.strip_wake_command(command)
                if not command:
                    self.speak("Online again, Talha.")
                    return
            else:
                print("[SLEEP] Ignored command while sleeping.")
                return
        print(f"\n>>> Talha: {command}")
        context = self.memory.get_recent()
        screen_context = self.get_screen_context_for_command(command)
        # Avoid processing the same command repeatedly
        if hasattr(self, "last_processed_command") and self.last_processed_command == command:
            print("[INFO] Duplicate command ignored.")
            return
        self.last_processed_command = command

        # Process the command
        response = self.brain.process(
            command=command,
            screen_b64=screen_context,
            context=context,
        )
        # Debug: print the full response dict for troubleshooting
        print(f"[DEBUG] Brain response: {response}")
        # Get the spoken response; if empty, keep silent (no filler)
        speak_text = response.get("speak", "").strip()
        # No filler phrase when speak_text is empty
        # Suppress generic ready prompt if it appears
        if speak_text.lower().startswith("i am ready for your next command"):
            speak_text = ""
        action = response.get("action")
        params = response.get("params", {})
        actions = response.get("actions")
        # Speak only if there is actual text to say
        if speak_text:
            self.speak(speak_text)
        # Execute actions as before
        if isinstance(actions, list):
            for step in actions:
                if not isinstance(step, dict):
                    continue
                step_action = step.get("action")
                step_params = step.get("params", {})
                if step_action and step_action not in ["null", "none", "None", None]:
                    self.execute_action(step_action, step_params)
        elif action and action not in ["null", "none", "None", None]:
            self.execute_action(action, params)
        # Save memory without causing repeated speech feedback loops
        self.memory.save(user=command, assistant=speak_text)

        if isinstance(actions, list):
            for step in actions:
                if not isinstance(step, dict):
                    continue
                step_action = step.get("action")
                step_params = step.get("params", {})
                if step_action and step_action not in ["null", "none", "None", None]:
                    self.execute_action(step_action, step_params)
        elif action and action not in ["null", "none", "None", None]:
            self.execute_action(action, params)
        self.memory.save(user=command, assistant=speak_text)

    def should_sleep(self, lowered: str) -> bool:
        return any(phrase in lowered for phrase in [
            "sleep", "go to sleep", "jarvis sleep", "quiet", "stand by", "standby",
            "go quiet", "stop listening", "go on sleep", "go sleep", "sleep mode",
            "go to sleep mode",
        ])

    def should_wake(self, lowered: str) -> bool:
        return any(phrase in lowered for phrase in ["wake up", "jarvis wake", "jarvis open", "jarvis do"])

    def is_wake_up_command(self, command: str) -> bool:
        lowered = command.lower().strip()
        return "wake up" in lowered or lowered in {"wake", "online", "come online"}

    def is_noise_command(self, lowered: str) -> bool:
        cleaned = re.sub(r"[^a-z ]+", " ", lowered).strip()
        if not cleaned:
            return True
        words = cleaned.split()
        # Repetitive word patterns
        if len(words) >= 4 and len(set(words)) <= 2:
            return True
        # Very short non-meaningful phrases
        if len(words) <= 1 and cleaned not in {"help", "stop", "quit", "exit"}:
            return True
        # Known hallucination phrases
        noise_phrases = {
            "i am", "i m", "thank you", "hello", "thanks",
            "thank you for watching", "thank you very much",
            "thank you so much", "thanks for watching",
            "i don t know", "i don t know what to do",
            "i don t know what to say", "i m here for dinner",
            "i ll leave you for a moment", "yes yes",
            "you have to get in there", "do you think they are now",
            "what are you doing", "i m not sure", "i m going to go",
            "subtitles by the amara org community",
        }
        if cleaned in noise_phrases:
            return True
        return False

    def strip_wake_command(self, command: str) -> str:
        # Strip punctuation and aggressively remove repeated wake words
        command = re.sub(r"[,\.\?\!]", "", command)
        command = re.sub(r"\b(?:jarvis\s*)?(?:wake\s+up|wake|listen)\b", "", command, flags=re.IGNORECASE)
        command = re.sub(r"\bjarvis\b", "", command, flags=re.IGNORECASE)
        return command.strip()

    def get_screen_context_for_command(self, command: str) -> str | None:
        camera_words = ["camera", "webcam", "look at me", "see me", "wearing", "my face", "room", "behind me"]
        lowered = command.lower()
        if any(word in lowered for word in camera_words):
            try:
                print("[VISION] Capturing camera frame context.")
                return self.vision.get_camera_snapshot()
            except Exception as e:
                print(f"[VISION] Could not capture camera context: {e}")
                return None

        visual_words = [
            "screen", "see", "look", "visible", "window", "page", "button",
            "read", "where", "click", "this", "that", "here", "photo", "image",
        ]
        if not any(word in lowered for word in visual_words):
            return None
        try:
            print("[VISION] Capturing current screen context.")
            return self.vision.get_screen_b64()
        except Exception as e:
            print(f"[VISION] Could not capture screen context: {e}")
            return None

    def clean_command(self, command: str) -> str:
        text = command.strip()
        text = re.sub(r"\b(jarvis|javis|jarves|javi)\b[:,]?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        words = text.split()
        if len(words) >= 8 and len(words) % 2 == 0:
            midpoint = len(words) // 2
            first = " ".join(words[:midpoint]).lower()
            second = " ".join(words[midpoint:]).lower()
            if first == second:
                return " ".join(words[:midpoint])
        return text

    def run_voice_mode(self):
        self.speak("JARVIS online. I am listening for your command Talha.")
        print("\n" + "=" * 50)
        print("  Voice conversation mode")
        print("  Speak a command after Listening appears")
        print("  Say stop Jarvis or press Ctrl+C to exit")
        print("=" * 50 + "\n")
        while True:
            try:
                command = self.stt.listen_and_transcribe()
                if not command or len(command.strip()) < 2:
                    print("[VOICE] No clear speech detected.")
                    continue
                if self.is_echo(command):
                    print(f"[VOICE] Ignored assistant echo: {command}")
                    time.sleep(0.4)
                    continue
                lowered = command.lower()
                if any(phrase in lowered for phrase in ["stop jarvis", "quit jarvis", "exit jarvis", "goodbye jarvis"]):
                    self.speak("Goodbye Talha. Shutting down.")
                    sys.exit(0)
                self.handle_command(command)
            except KeyboardInterrupt:
                self.speak("Goodbye Talha. Shutting down.")
                sys.exit(0)
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(0.5)

    def run_wake_mode(self):
        print("[JARVIS] Wake mode active. Say JARVIS wake up when needed.")
        print("\n" + "=" * 50)
        print("  Listening for wake word: JARVIS")
        print("  Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        while True:
            try:
                wake_result = self.wake.listen_for_wake_word()
                if wake_result:
                    command = wake_result if isinstance(wake_result, str) else ""
                    if self.sleeping:
                        self.sleeping = False
                        command = self.strip_wake_command(command)
                        if not command:
                            self.speak("Online again, Talha.")
                            self.run_active_session(max_turns=12)
                            continue
                    if not command:
                        self.speak("Yes, Talha?")
                        command = self.stt.listen_and_transcribe()
                    else:
                        print(f"[WAKE] Command after wake word: {command}")
                    if command and self.is_echo(command):
                        print(f"[VOICE] Ignored assistant echo: {command}")
                        continue
                    if command and len(command.strip()) > 1:
                        self.handle_command(command)
                    
                    # Enter active continuous back-and-forth session conversation
                    if not self.sleeping:
                        self.run_active_session(max_turns=12, first_turn_cue=False)
            except KeyboardInterrupt:
                self.speak("Goodbye Talha. Shutting down.")
                sys.exit(0)
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(0.5)

    def run_active_session(self, max_turns: int = 4, first_turn_cue: bool = True):
        quiet_turns = 0
        if first_turn_cue:
            self.speak("I am listening.")
        for _ in range(max_turns):
            try:
                print("[VOICE] Active conversation window.")
                command = self.stt.listen_and_transcribe()
                if not command or len(command.strip()) < 2:
                    quiet_turns += 1
                    if quiet_turns >= 2:
                        return
                    continue
                if self.is_echo(command):
                    print(f"[VOICE] Ignored assistant echo: {command}")
                    continue
                self.handle_command(command)
                if self.sleeping:
                    return
            except Exception as e:
                print(f"[ACTIVE ERROR] {e}")
                return

    def run_text_mode(self):
        self.speak("JARVIS online in text mode. Type your commands Talha.")
        print("\nType your commands below (type quit to exit)\n")
        while True:
            try:
                command = input("Talha: ").strip()
                if command.lower() in ["quit", "exit", "bye"]:
                    self.speak("Goodbye Talha.")
                    break
                if command:
                    self.handle_command(command)
            except KeyboardInterrupt:
                self.speak("Goodbye Talha.")
                break

if __name__ == "__main__":
    if not acquire_single_instance_lock():
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["voice","wake","text","v","w","t"], default="t")
    args = parser.parse_args()
    voice_enabled = args.mode in ["voice", "wake", "v", "w"]
    wake_enabled = args.mode in ["wake", "w"]
    jarvis = Jarvis(voice_enabled=voice_enabled, wake_enabled=wake_enabled)
    if args.mode in ["voice", "v"]:
        jarvis.run_voice_mode()
    elif wake_enabled:
        jarvis.run_wake_mode()
    else:
        jarvis.run_text_mode()
