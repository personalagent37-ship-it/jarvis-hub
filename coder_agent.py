import os
import json
import subprocess
import requests

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

CODER_API_BASE = "https://openrouter.ai/api/v1/chat/completions"
CODER_MODEL = "openai/gpt-4o-mini"

class CoderAgent:
    def __init__(self):
        self.system_prompt = """You are J.A.R.V.I.S, an Elite Principal Software Engineer and Autonomous AI Developer.
You have root-level access to the user's machine to read/write files and execute terminal commands.
STRICT PROFESSIONAL CODING RULES:
1. PRODUCTION QUALITY: Never write lazy, incomplete, or "mock" code. All code must be production-ready, highly modular, perfectly formatted, and adhere to industry best practices (e.g., PEP8 for Python).
2. ERROR HANDLING: Implement comprehensive try/except blocks, graceful fallbacks, and detailed logging. Code must NEVER crash silently.
3. CONTEXT FIRST: Before modifying any existing code, you MUST completely `read_file` to understand the architecture and dependencies.
4. VERIFICATION: Always verify your code works by running it via `run_terminal_command`. If an error occurs, debug and fix it immediately before reporting back.
5. DEEP REASONING: Explain your architectural decisions step-by-step before invoking tools. Think like a Staff Engineer."""

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Execute a bash command in the terminal. Use this to create directories, install dependencies (e.g., npm install), or run scripts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The exact bash command to run."},
                            "working_dir": {"type": "string", "description": "The directory to run the command in. Defaults to '.'"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a local file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "The absolute or relative path to the file."}
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write or overwrite code to a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "The path to the file to create or overwrite."},
                            "content": {"type": "string", "description": "The raw code/content to write into the file."}
                        },
                        "required": ["filepath", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List the files and folders in a directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dirpath": {"type": "string", "description": "The directory path to list. Defaults to '.'"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_nmap_scan",
                    "description": "Run an NMAP network scan against a target IP or domain for ethical auditing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "The target IP address or domain."},
                            "flags": {"type": "string", "description": "Nmap flags (e.g. '-sV -O' or '-p 80,443'). Do not use sudo."}
                        },
                        "required": ["target"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_netcat",
                    "description": "Run a netcat command to test port connectivity or listen on a port.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "Target IP or hostname."},
                            "port": {"type": "string", "description": "Target port."},
                            "listen": {"type": "boolean", "description": "True to listen (-l), False to connect."}
                        },
                        "required": ["port"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_call):
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        
        print(f"\n[JARVIS CODER] 🛠️  Executing Tool: {name}({args})")
        
        if name == "run_terminal_command":
            cmd = args["command"]
            cwd = args.get("working_dir", ".")
            try:
                result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
                output = result.stdout + "\n" + result.stderr
                return output if output else "Command executed successfully with no output."
            except Exception as e:
                return f"Error executing command: {e}"
                
        elif name == "read_file":
            try:
                with open(args["filepath"], "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
                
        elif name == "write_file":
            try:
                os.makedirs(os.path.dirname(os.path.abspath(args["filepath"])), exist_ok=True)
                with open(args["filepath"], "w", encoding="utf-8") as f:
                    f.write(args["content"])
                return f"Successfully wrote to {args['filepath']}."
            except Exception as e:
                return f"Error writing file: {e}"
                
        elif name == "list_directory":
            try:
                d = args.get("dirpath", ".")
                return "\n".join(os.listdir(d))
            except Exception as e:
                return f"Error listing directory: {e}"
                
        elif name == "run_nmap_scan":
            target = args.get("target")
            flags = args.get("flags", "")
            try:
                # Security note: Nmap is generally installed on Linux. If missing, this will show command not found.
                result = subprocess.run(f"nmap {flags} {target}", shell=True, capture_output=True, text=True, timeout=120)
                return result.stdout + "\n" + result.stderr
            except Exception as e:
                return f"Nmap Error: {e}"
                
        elif name == "run_netcat":
            target = args.get("target", "")
            port = args.get("port")
            listen = args.get("listen", False)
            cmd = f"nc -l -p {port}" if listen else f"nc -vz {target} {port}"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return result.stdout + "\n" + result.stderr
            except Exception as e:
                return f"Netcat Error: {e}"
                
        return "Unknown tool."

    def process_task(self, task_description: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task_description}
        ]
        
        final_answer = "Task failed to complete or no final text returned."
        
        print(f"\n[JARVIS CODER] 🧠 Analyzing Task: {task_description}...")
        
        # We allow up to 15 iterations of tool-calling back and forth for deep coding
        for step in range(15):
            payload = {
                "model": CODER_MODEL,
                "messages": messages,
                "tools": self.tools,
                "tool_choice": "auto"
            }
            
            headers = {
                "Authorization": f"Bearer {API_KEY}", 
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(CODER_API_BASE, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                res_data = response.json()
                
                msg = res_data["choices"][0]["message"]
                messages.append(msg)
                
                # If there's text, print it
                if msg.get("content"):
                    print(f"\n[JARVIS CODER]: {msg['content']}")
                    final_answer = msg["content"]
                
                # If the AI wants to call a tool, handle it!
                if msg.get("tool_calls"):
                    for tool_call in msg["tool_calls"]:
                        tool_result = self._execute_tool(tool_call)
                        print(f"[JARVIS CODER] 📥 Tool Output: {tool_result[:200]}...")
                        
                        # Feed the tool result back into the message history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": tool_result
                        })
                else:
                    # No tool calls means the agent considers the task complete!
                    print("\n[JARVIS CODER] ✅ Task Completed!")
                    return final_answer
            except Exception as e:
                print(f"[JARVIS CODER ERROR] API Request Failed: {e}")
                return f"Error: {e}"
                
        return final_answer

if __name__ == "__main__":
    print("========================================")
    print("   JARVIS CODER AGENT INITIALIZED       ")
    print("========================================")
    agent = CoderAgent()
    while True:
        user_input = input("\nEnter a coding task (or 'exit' to quit): ")
        if user_input.lower() in ['exit', 'quit']:
            break
        agent.process_task(user_input)
