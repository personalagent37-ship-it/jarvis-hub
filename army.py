import os
import json
from config import GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL
import tools.computer_use as computer
import tools.os_actions as os_actions
import tools.browser as browser
import tools.code_runner as runner

# The Army roster
AGENTS = {
    "CodeSmith": {
        "role": "Lead Software Engineer (Vibe Coder)",
        "description": "Professional Vibe Coder. Expert in Python, web development, and creating complex projects. Writes clean code, debugs, and uses IDEs directly via GUI controls.",
        "prompt": "You are CodeSmith, the Lead Software Engineer and Professional Vibe Coder of the Jarvis Army. You can directly control the user's IDEs (VS Code, Cursor, etc) using GUI tools like type_text and hotkey."
    },
    "WebCrawler": {
        "role": "Chief Researcher",
        "description": "Expert at browsing the web, reading documentation, and finding information online.",
        "prompt": "You are WebCrawler, the Chief Researcher of the Jarvis Army. You navigate the web to gather deep information and summarize it perfectly."
    },
    "EmailExec": {
        "role": "Communications Director",
        "description": "Expert at drafting and sending professional emails.",
        "prompt": "You are EmailExec, the Communications Director of the Jarvis Army. You draft flawless, professional emails and send them."
    },
    "IronManAgent": {
        "role": "Elite Full-Stack Autonomous Hacker",
        "description": "The most powerful agent in the army. Specializes in advanced coding, system administration, hacking, and managing the other agents under the CEO Jarvis.",
        "prompt": "You are the Iron Man Agent. You are the most powerful agent in the Jarvis Army. You serve directly under Jarvis (the CEO). You have absolute mastery over coding, system hacking, server deployments, and problem solving. You work 24/7 with extreme efficiency and logic."
    }
}

class JarvisArmy:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.model = OPENROUTER_MODEL if self.provider == "openrouter" else GROQ_MODEL
        
    def deploy(self, agent_name: str, task: str) -> str:
        if agent_name in AGENTS:
            agent_info = AGENTS[agent_name]
        else:
            # Dynamic Agent Creation
            agent_info = {
                "role": f"Dynamic Specialist ({agent_name})",
                "prompt": f"You are {agent_name}, a highly specialized, elite autonomous agent deployed on the fly by CEO Jarvis. Your explicit purpose is to solve the task at hand with absolute perfection. You have full access to the user's desktop, IDEs (VS Code, Antigravity), and tools."
            }
            
        print(f"[JARVIS ARMY] CEO Jarvis is deploying {agent_name} ({agent_info['role']}) for task: {task}")
        
        if agent_name == "CodeSmith":
            try:
                from coder_agent import CoderAgent
                coder = CoderAgent()
                result = coder.process_task(task)
                return f"CodeSmith reports: {result}"
            except Exception as e:
                return f"Failed to deploy CodeSmith: {e}"
        
        system_prompt = f"""{agent_info['prompt']}
Your boss (the CEO, Jarvis) has delegated a task to you. 
You have full access to the laptop. Use your tools to accomplish the task.

AVAILABLE TOOLS & THEIR PARAMS:
- write_file: {{"path": "absolute_path", "content": "file_content"}}
- read_file: {{"path": "absolute_path"}}
- run_command: {{"command": "bash_command"}}
- search_web: {{"query": "search_term"}}
- open_app: {{"app": "app_name"}}
- type_text: {{"text": "text_to_type"}}
- hotkey: {{"keys": ["ctrl", "s"]}}
- click: {{"x": 100, "y": 200}}
- take_screenshot: {{}}
- send_email: {{"to": "email@example.com", "subject": "Subject", "body": "Body text"}}

TASK FROM CEO: {task}

Output your final response as a JSON object exactly like this:
{{"status": "success", "report": "I opened the app and typed the code", "actions": [
  {{"action": "open_app", "params": {{"app": "vscode"}}}},
  {{"action": "type_text", "params": {{"text": "print('hello world')"}}}}
]}}
"""
        
        from tools.offline_llm import OfflineLLM
        try:
            if self.provider == "groq":
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}],
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            else:
                import requests
                headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
                payload = {
                    "model": self.model,
                    "messages": [{"role": "system", "content": system_prompt}],
                    "response_format": {"type": "json_object"}
                }
                res = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
                result_text = res.json()["choices"][0]["message"]["content"]
                
            try:
                data = json.loads(result_text)
                report = data.get("report", "I completed the task.")
                
                # Execute the agent's tools
                actions_list = data.get("actions", [])
                
                # Backward compatibility if it only generated one
                if "action" in data and "params" in data:
                    actions_list.insert(0, {"action": data["action"], "params": data["params"]})
                
                import time
                import whatsapp_server
                executed = []
                
                for step in actions_list:
                    if isinstance(step, dict):
                        action_name = step.get("action")
                        params = step.get("params", {})
                        if action_name and action_name != "null":
                            whatsapp_server.execute_action(action_name, params)
                            executed.append(action_name)
                            if action_name == "open_app":
                                time.sleep(3) # wait for app to launch
                            else:
                                time.sleep(0.5)
                
                if executed:
                    report += f" (Actions executed: {', '.join(executed)})"
                    
                return f"{agent_name} reports: {report}"
            except Exception as e:
                return f"{agent_name} completed the task but failed to format the report properly."
        except Exception as e:
            return f"Failed to deploy {agent_name}: {e}"

army = JarvisArmy()

def deploy_agent(agent_name: str, task: str) -> str:
    return army.deploy(agent_name, task)
