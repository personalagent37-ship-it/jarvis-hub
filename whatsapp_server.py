#!/usr/bin/env python3
import os
import re
import json
from flask import Flask, request
import requests
from dotenv import load_dotenv

# Global dict for continuous auto-reply features
# Format: {"contact_id": {"name": "Contact Name", "persona": "Iron Man etc"}}
AUTO_REPLY_TARGETS = {}

# Import Jarvis tools
from brain import JarvisBrain
from memory import Memory
from tools.os_actions import OSActions
import tools.computer_use as computer
import tools.browser as browser
import tools.system_control as sysctl
import tools.file_manager as files
import tools.code_runner as runner
import tools.system_info as sysinfo
import tools.email_tool as email_tool
from tools.car_control import CarControl
from tools.home_automation import HomeAutomation
from vision import Vision
import army

load_dotenv()

app = Flask(__name__)
brain = JarvisBrain()
memory = Memory()
os_actions = OSActions()
car_control = CarControl()
home_automation = HomeAutomation()
vision = Vision()



def send_whatsapp_message_to_contact(contact_name: str, message: str, media_base64: str = None) -> str:
    if not contact_name or not message:
        return "Failed: contact_name and message are required."
    try:
        import requests
        contacts_res = requests.get("http://localhost:3000/api/contacts", timeout=5).json()
        target = None
        
        numeric_target = ''.join(filter(str.isdigit, contact_name))
        is_raw_number = len(numeric_target) >= 10 and len(numeric_target) > (len(contact_name) * 0.5)

        # Pass 1: Try exact match (case-insensitive)
        for c in contacts_res:
            if contact_name.lower() == str(c.get("name", "")).lower():
                target = c["id"]
                break
                
        # Pass 2: If it's a raw phone number, just use it!
        if not target and is_raw_number:
            # Check if it matches an existing contact's ID first
            for c in contacts_res:
                c_num = ''.join(filter(str.isdigit, str(c.get("id", ""))))
                if numeric_target in c_num:
                    target = c["id"]
                    break
            # If still not found, construct a generic WhatsApp ID so we can message unsaved numbers
            if not target:
                target = f"{numeric_target}@c.us"
                
        # Pass 3: Fuzzy string matching (only if not a raw number)
        if not target and not is_raw_number:
            import difflib
            contact_names = [str(c.get("name", "")) for c in contacts_res if c.get("name")]
            # Use a strict cutoff of 0.75 so we don't accidentally message the wrong person!
            matches = difflib.get_close_matches(contact_name, contact_names, n=1, cutoff=0.75)
            if matches:
                best_match = matches[0]
                for c in contacts_res:
                    if str(c.get("name", "")) == best_match:
                        target = c["id"]
                        contact_name = best_match # Update name for logging
                        break
                        
        # Pass 4: Safe Substring match (fallback)
        if not target and not is_raw_number and len(contact_name) >= 3:
            for c in contacts_res:
                if contact_name.lower() in str(c.get("name", "")).lower():
                    target = c["id"]
                    contact_name = str(c.get("name", ""))
                    break
                        
        if not target:
            return f"Failed: Could not find contact matching '{contact_name}'"
        
        send_payload = {"to": target, "message": message}
        if media_base64:
            send_payload["mediaBase64"] = media_base64
            
        requests.post("http://localhost:3000/send", json=send_payload, timeout=5)
        return f"Message sent to {contact_name} successfully."
    except Exception as e:
        return f"Failed to send message: {e}"

def start_auto_reply(contact_name: str, persona: str) -> str:
    try:
        res = requests.get("http://localhost:3000/api/contacts", timeout=5)
        contacts_res = res.json()
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return "Failed to fetch contacts from Hub."
    target = None
    # Pass 1: exact match
    for c in contacts_res:
        if contact_name.lower() == str(c.get("name", "")).lower():
            target = c["id"]
            break
    # Pass 2: Fuzzy string matching
    if not target:
        import difflib
        contact_names = [str(c.get("name", "")) for c in contacts_res if c.get("name")]
        matches = difflib.get_close_matches(contact_name, contact_names, n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            for c in contacts_res:
                if str(c.get("name", "")) == best_match:
                    target = c["id"]
                    contact_name = best_match
                    break
    if not target:
        return f"Could not find a contact matching '{contact_name}'."
    
    AUTO_REPLY_TARGETS[target] = {"name": contact_name, "persona": persona}
    return f"Started continuously replying to {contact_name} as '{persona}'."

def stop_auto_reply(contact_name: str) -> str:
    # We can just remove it by name roughly
    keys_to_del = []
    for k, v in AUTO_REPLY_TARGETS.items():
        if contact_name.lower() in v["name"].lower():
            keys_to_del.append(k)
    if not keys_to_del:
        return f"No active auto-reply found for {contact_name}."
    for k in keys_to_del:
        del AUTO_REPLY_TARGETS[k]
    return f"Stopped continuously replying to {contact_name}."

def execute_action(action: str, params: dict):
    if not action or action in ["null", "none", "None"]:
        return ""
    params = params or {}
    
    # We map a subset of safe/useful actions for remote WhatsApp usage
    action_map = {
        # GUI Control
        "click":              lambda p: computer.click(**p),
        "type_text":          lambda p: computer.type_text(**p),
        "hotkey":             lambda p: computer.hotkey(**p),
        "scroll":             lambda p: computer.scroll(**p),
        "take_screenshot":    lambda p: computer.take_screenshot(),
        
        # Apps & Browser
        "open_app":           lambda p: os_actions.open_app(p.get('app')),
        "open_terminal":      lambda p: computer.open_terminal(),
        "browse_url":         lambda p: browser.navigate(**p),
        "search_web":         lambda p: browser.search_web(**p),
        "open_mail":          lambda p: browser.open_mail(),
        "search_mail":        lambda p: browser.search_mail(),
        "read_mail_page":     lambda p: browser.read_mail_page(),
        "prepare_email":      lambda p: browser.prepare_email(**p),
        "send_email":         lambda p: email_tool.send_email(p.get("to"), p.get("subject"), p.get("body")),
        "prepare_whatsapp_message": lambda p: browser.prepare_whatsapp_message(**p),
        "start_whatsapp_call": lambda p: browser.start_whatsapp_call(**p),
        
        # File Operations
        "read_file":          lambda p: os_actions.read_file(p.get('path')),
        "write_file":         lambda p: os_actions.write_file(p.get('path'), p.get('content')),
        "append_file":        lambda p: os_actions.append_file(p.get('path'), p.get('content')),
        "create_folder":      lambda p: os_actions.create_folder(p.get('path')),
        "delete_file":        lambda p: os_actions.delete_file(p.get('path')),
        "copy_file":          lambda p: os_actions.copy_file(p.get('source'), p.get('dest')),
        "move_file":          lambda p: os_actions.move_file(p.get('source'), p.get('dest')),
        "list_files":         lambda p: os_actions.list_files(p.get('path')),
        "search_files":       lambda p: os_actions.search_files(p.get('pattern'), p.get('path')),
        "get_file_info":      lambda p: os_actions.get_file_info(p.get('path')),
        "set_permissions":    lambda p: files.set_permissions(**p),
        
        # System Info
        "get_system_info":    lambda p: sysinfo.get_system_info(),
        "get_processes":      lambda p: sysinfo.get_running_processes(),
        "get_network_info":   lambda p: sysinfo.get_network_info(),
        "get_battery_info":   lambda p: sysinfo.get_battery_info(),
        "describe_screen":    lambda p: vision.get_screen_text(),
        
        # System Control
        "shutdown":           lambda p: sysctl.shutdown(**p),
        "reboot":             lambda p: sysctl.reboot(**p),
        "lock_screen":        lambda p: sysctl.lock_screen(),
        "unlock_screen":      lambda p: sysctl.unlock_screen(p.get("password")),
        "suspend":            lambda p: sysctl.suspend(),
        "start_service":      lambda p: sysctl.start_service(**p),
        "stop_service":       lambda p: sysctl.stop_service(**p),
        "restart_service":    lambda p: sysctl.restart_service(**p),
        "kill_process":       lambda p: sysctl.kill_process(**p),
        
        # Code Execution
        "run_command":        lambda p: os_actions.run_command(p.get('command')),
        "run_python":         lambda p: runner.run_python(**p),
        "install_package":    lambda p: os_actions.install_package(p.get('package')),
        "list_packages":      lambda p: os_actions.list_packages(),
        "run_script":         lambda p: runner.run_script(**p),
        
        # Clipboard
        "get_clipboard":      lambda p: sysctl.get_clipboard(),
        "clear_clipboard":    lambda p: sysctl.clear_clipboard(),
        
        # Car Control
        "lock_car":           lambda p: car_control.lock(),
        "unlock_car":         lambda p: car_control.unlock(),
        "start_charge":       lambda p: car_control.start_charge(),
        "stop_charge":        lambda p: car_control.stop_charge(),
        "set_climate":        lambda p: car_control.set_climate(p.get('temperature')),
        
        # Home Automation
        "ha_turn_on":         lambda p: home_automation.turn_on(p.get('entity_id')),
        "ha_turn_off":        lambda p: home_automation.turn_off(p.get('entity_id')),
        "ha_set_brightness":  lambda p: home_automation.set_brightness(p.get('entity_id'), p.get('brightness')),
        "ha_set_temperature": lambda p: home_automation.set_temperature(p.get('entity_id'), p.get('temperature')),
        
        # Persistent Memory
        "save_fact":          lambda p: (memory.save_fact(p.get("key"), p.get("value")), f"Saved fact: {p.get('key')} = {p.get('value')}")[1],
        "get_fact":           lambda p: memory.get_fact(p.get("key")) or "I do not remember that.",
        
        # Vision
        "camera_snapshot":    lambda p: vision.get_camera_snapshot(),
        
        # Army
        "deploy_army":        lambda p: army.deploy_agent(p.get('agent'), p.get('task')),
        
        # WhatsApp Messaging
        "send_message":       lambda p: send_whatsapp_message_to_contact(p.get("contact_name"), p.get("message"), p.get("media_base64")),
        "start_auto_reply":   lambda p: start_auto_reply(p.get("contact_name"), p.get("persona")),
        "stop_auto_reply":    lambda p: stop_auto_reply(p.get("contact_name")),
    }
    
    func = action_map.get(action)
    if func:
        try:
            print(f"[WHATSAPP ACTION] Executing {action} with {params}")
            return func(params)
        except Exception as e:
            print(f"[WHATSAPP ACTION ERROR] {e}")
            return f"Error executing {action}: {e}"
    else:
        print(f"[WHATSAPP ACTION] Unknown action: {action}")
    return ""

@app.route("/whatsapp_local", methods=["POST"])
def whatsapp_webhook():
    data = request.json or {}
    incoming_msg = data.get("Body", "").strip()
    sender = data.get("From", "")
    is_self_chat = data.get("isSelfChat", True) # Default to true for backward compatibility
    
    print(f"\n[WHATSAPP] Received from {sender} (isSelfChat={is_self_chat}): {incoming_msg}")
    
    if not incoming_msg:
        return "OK", 200
        
    # DIRECT CODER AGENT INTERCEPTION
    if incoming_msg.lower().startswith("coder:"):
        print(f"[WHATSAPP] Routing task directly to CoderAgent...")
        try:
            import sys
            import requests
            if "/home/talha/Desktop/jartvis" not in sys.path:
                sys.path.append("/home/talha/Desktop/jartvis")
            from coder_agent import CoderAgent
            agent = CoderAgent()
            task_desc = incoming_msg[6:].strip()
            # Send an immediate processing message
            requests.post("http://localhost:3000/send", json={"to": sender, "message": "⚙️ [Coder Agent] Processing your request..."}, timeout=5)
            # Run the task synchronously (this can take up to 60s)
            result = agent.process_task(task_desc)
            # Send the result
            requests.post("http://localhost:3000/send", json={"to": sender, "message": "💻 [Coder Agent Final Result]:\n\n" + str(result)}, timeout=5)
        except Exception as e:
            requests.post("http://localhost:3000/send", json={"to": sender, "message": f"❌ [Coder Agent Error]: {e}"}, timeout=5)
        return "OK", 200

    # If it's a message from someone else, we check if they are an auto-reply target
    if not is_self_chat:
        if sender in AUTO_REPLY_TARGETS:
            persona = AUTO_REPLY_TARGETS[sender]["persona"]
            print(f"[AUTO-REPLY] Replying to {sender} as {persona}")
            try:
                # Use OpenRouter to generate the reply
                from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL
                import requests
                headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
                prompt = f"You are acting as: {persona}\nThe user says: {incoming_msg}\nReply strictly in character, briefly and naturally as this is a WhatsApp chat. Do not add quotes around your response."
                payload = {
                    "model": OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
                reply_text = res.json()["choices"][0]["message"]["content"].strip(' "')
                
                # Send it!
                requests.post("http://localhost:3000/send", json={"to": sender, "message": reply_text}, timeout=5)
            except Exception as e:
                print(f"[AUTO-REPLY ERROR] {e}")
        return "OK", 200

    # Check for pending confirmations
    pending_str = memory.get_fact("pending_whatsapp_action")
    if pending_str and pending_str.strip():
        lower_msg = incoming_msg.lower().strip()
        if lower_msg in ["yes", "yeah", "yep", "do it", "proceed", "ok", "sure"]:
            try:
                pending = json.loads(pending_str)
                action_name = pending.get("action")
                action_params = pending.get("params", {})
                actions_list = pending.get("actions")
                
                action_results = []
                media_base64 = None
                
                if isinstance(actions_list, list):
                    for step in actions_list:
                        if isinstance(step, dict):
                            step_action = step.get("action")
                            step_params = step.get("params", {})
                            if step_action and step_action not in ["null", "none", "None", None]:
                                print(f"[WHATSAPP] User confirmed multi-action: {step_action}")
                                res = execute_action(step_action, step_params)
                                if step_action == "camera_snapshot" and res:
                                    media_base64 = res
                                    action_results.append("Captured camera snapshot.")
                                elif res: 
                                    action_results.append(str(res))
                elif action_name and action_name not in ["null", "none", "None", None]:
                    print(f"[WHATSAPP] User confirmed action: {action_name}")
                    res = execute_action(action_name, action_params)
                    if action_name == "camera_snapshot" and res:
                        media_base64 = res
                        action_results.append("Captured camera snapshot.")
                    elif res: 
                        action_results.append(str(res))
                    
                memory.save_fact("pending_whatsapp_action", "") # clear it
                reply_text = f"Action(s) completed.\n" + "\n".join(action_results) if action_results else "Action(s) completed."
                
                try:
                    res = requests.post("http://localhost:3000/send", json={
                        "to": sender, 
                        "message": reply_text,
                        "mediaBase64": media_base64
                    }, timeout=10)
                    print(f"[DEBUG] Sent reply to hub, status {res.status_code}")
                except Exception as e:
                    print(f"[ERROR] Failed to send action result to Hub: {e}")
                return "OK", 200
            except Exception as e:
                reply_text = f"Error executing action: {e}"
                memory.save_fact("pending_whatsapp_action", "")
            
            try:
                requests.post("http://localhost:3000/send", json={"to": sender, "message": reply_text}, timeout=5)
            except Exception:
                pass
            return "OK", 200
            
        elif lower_msg in ["no", "cancel", "stop", "nevermind", "abort"]:
            memory.save_fact("pending_whatsapp_action", "")
            try:
                requests.post("http://localhost:3000/send", json={"to": sender, "message": "Action cancelled."}, timeout=5)
            except Exception:
                pass
            return "OK", 200

    # 1. Process command via Brain
    context = memory.get_recent()
    # (Removed recent_inbound injection to prevent LLM hallucinations)
    
    response = brain.process(
        command=incoming_msg,
        screen_b64=None,
        context=context,
    )
    
    print(f"[DEBUG] Brain response: {response}")
    
    speak_text = response.get("speak", "").strip()
    action = response.get("action")
    params = response.get("params", {})
    actions = response.get("actions")
    
    # 2. Check if we need to execute an action
    has_action = False
    media_base64 = None
    if isinstance(actions, list) and len(actions) > 0:
        has_action = True
    elif action and action not in ["null", "none", "None", None]:
        has_action = True
        
    if has_action:
        # Check if the action requires permission (e.g. messaging people)
        # Auto-execute safe actions immediately!
        action_results = []
        media_base64 = None
        
        DANGEROUS_ACTIONS = ["send_message", "send_whatsapp_message", "start_auto_reply", "start_whatsapp_call"]
        
        if isinstance(actions, list):
            for step in actions:
                if isinstance(step, dict):
                    step_action = step.get("action")
                    step_params = step.get("params", {})
                    if step_action and step_action not in ["null", "none", "None", None]:
                        if step_action in DANGEROUS_ACTIONS:
                            memory.save_fact("pending_whatsapp_action", json.dumps({"action": step_action, "params": step_params}))
                            reply_text = f"{speak_text}\n\n[SECURITY] Do you want me to execute '{step_action}'? Reply 'yes' to confirm."
                            memory.save(user=incoming_msg, assistant=reply_text)
                            requests.post("http://localhost:3000/send", json={"to": sender, "message": reply_text}, timeout=5)
                            return "OK", 200

                        print(f"[WHATSAPP] Auto-executing multi-action: {step_action}")
                        if step_action == "send_message" and media_base64:
                            step_params["media_base64"] = media_base64
                            
                        res = execute_action(step_action, step_params)
                        if step_action == "camera_snapshot" and res:
                            media_base64 = res
                            action_results.append("Captured camera snapshot.")
                        elif res: 
                            action_results.append(str(res))
        elif action and action not in ["null", "none", "None", None]:
            if action in DANGEROUS_ACTIONS:
                memory.save_fact("pending_whatsapp_action", json.dumps({"action": action, "params": params}))
                reply_text = f"{speak_text}\n\n[SECURITY] Do you want me to execute '{action}'? Reply 'yes' to confirm."
                memory.save(user=incoming_msg, assistant=reply_text)
                requests.post("http://localhost:3000/send", json={"to": sender, "message": reply_text}, timeout=5)
                return "OK", 200

            print(f"[WHATSAPP] Auto-executing action: {action}")
            if action == "send_message" and media_base64:
                params["media_base64"] = media_base64
                
            res = execute_action(action, params)
            if action == "camera_snapshot" and res:
                media_base64 = res
                action_results.append("Captured camera snapshot.")
            elif res: 
                action_results.append(str(res))
                
        reply_text = f"{speak_text}\n\n[Action Completed: " + " | ".join(action_results)[:300] + "]" if action_results else speak_text
        memory.save(user=incoming_msg, assistant=reply_text)
    else:
        # No action to take, just normal conversation
        reply_text = speak_text
        memory.save(user=incoming_msg, assistant=reply_text)
        
    if not reply_text:
        return "OK", 200

    # Send response back to Node.js Jarvis Hub
    try:
        requests.post("http://localhost:3000/send", json={
            "to": sender,
            "message": reply_text,
            "mediaBase64": media_base64
        }, timeout=5)
    except Exception as e:
        print(f"[ERROR] Could not send reply to Jarvis Hub: {e}")

    return "OK", 200

if __name__ == "__main__":
    print("="*50)
    print(" Starting JARVIS Python Local Webhook on port 5000...")
    print("="*50)
    app.run(host="0.0.0.0", port=5000, debug=False)
