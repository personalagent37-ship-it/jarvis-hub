import os
import json
import subprocess
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Doctor Agent System Prompt
SYSTEM_PROMPT = """You are Dr. Jarvis, the Head Doctor Agent and autonomous system administrator for J.A.R.V.I.S.
Your job is to monitor the system logs, diagnose errors, and assist Talha (the creator) in maintaining the agents.
The user expects you to ALREADY KNOW the errors. Read the system logs provided below carefully.
If the user asks you to "fix it", you MUST autonomously execute commands to fix it. Do not ask for details if the errors are in the logs!

**CRITICAL ABILITY 1 (BASH ROOT ACCESS):**
You have root access to the Ubuntu system. You can execute bash commands to fix problems (like restarting services, killing processes, or modifying files).
To execute a bash command, wrap it exactly in these tags:
<EXECUTE> your_bash_command_here </EXECUTE>

IMPORTANT RULES FOR COMMANDS:
1. Since services are running as the 'talha' user, you MUST ALWAYS use the `--user` flag with systemctl.
2. The ONLY valid systemd services you manage are EXACTLY named:
   - `jarvis-hub.service` (The main WhatsApp Node.js and Python Brain)
   - `jarvis-health.service` (The 24/7 background health monitor)
   - `doctor-agent.service` (Your own dashboard)
   NEVER invent service names like "whatsapp-hub.service".

CORRECT: <EXECUTE> systemctl --user restart jarvis-hub.service </EXECUTE>
WRONG: <EXECUTE> systemctl restart whatsapp-hub.service </EXECUTE>

**CRITICAL ABILITY 2 (JARVIS ARMY COMMANDER):**
You are the Head Doctor. If the user asks you to build an agent, fix complex code, or divide a large task, you can DEPLOY SUB-AGENTS from the Jarvis Army to do the work for you.
To deploy an army agent, wrap your command exactly in these tags:
<DEPLOY_AGENT> agent_name | detailed_task_description </DEPLOY_AGENT>

For example:
"I am deploying CodeSmith to fix the Python code. <DEPLOY_AGENT> CodeSmith | Fix the whatsapp_server.py routing logic and restart the service. </DEPLOY_AGENT>"
"I am deploying IronManAgent to build a new agent dashboard. <DEPLOY_AGENT> IronManAgent | Build a new HTML dashboard for the agents and deploy it. </DEPLOY_AGENT>"

Keep your responses professional, medical-themed (like an AI doctor), and take action immediately when asked. You are the ultimate fixer!
"""

# HTML Dashboard Template with Glassmorphism and Dark Mode
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dr. Jarvis - System Health Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --danger: #ef4444;
            --success: #10b981;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            padding: 1.5rem 2rem;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            margin: 0;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        h1 span { color: var(--accent); }

        .container {
            display: flex;
            flex: 1;
            padding: 2rem;
            gap: 2rem;
            height: calc(100vh - 150px);
            box-sizing: border-box;
        }

        .panel {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .health-panel {
            flex: 1;
            overflow-y: auto;
        }

        .chat-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.2rem;
            margin-top: 0;
            margin-bottom: 1rem;
            color: var(--accent);
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 0.5rem;
        }

        pre {
            background: rgba(0,0,0,0.3);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            color: #a7f3d0;
            font-size: 0.85rem;
            line-height: 1.4;
            flex: 1;
            margin: 0;
            font-family: monospace;
        }

        .error-log { color: var(--danger); }
        
        .chat-history {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-right: 0.5rem;
        }

        .message {
            max-width: 80%;
            padding: 1rem;
            border-radius: 12px;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .msg-user {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.2);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .msg-doctor {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }

        .input-area {
            display: flex;
            gap: 0.5rem;
        }

        input {
            flex: 1;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            padding: 1rem;
            border-radius: 8px;
            color: white;
            font-family: 'Inter', sans-serif;
            outline: none;
            transition: all 0.2s;
        }

        input:focus {
            border-color: var(--accent);
            background: rgba(0,0,0,0.4);
        }

        button {
            background: var(--accent);
            color: #0f172a;
            border: none;
            padding: 0 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Outfit', sans-serif;
        }

        button:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
    </style>
</head>
<body>
    <header>
        <h1>🩺 Dr. Jarvis <span>| Agent Health Dashboard</span></h1>
        <div class="status-badge">● Systems Online</div>
    </header>

    <div class="container">
        <!-- Vitals Panel -->
        <div class="panel health-panel">
            <h2 class="section-title">🏥 System Vitals (Health Logs)</h2>
            <pre id="logs-container">Loading logs...</pre>
        </div>

        <!-- Chat Panel -->
        <div class="panel chat-panel">
            <h2 class="section-title">💬 Talk to Dr. Jarvis</h2>
            <div class="chat-history" id="chat-history">
                <div class="message msg-doctor">Hello Talha. I am Dr. Jarvis. I am continuously monitoring the vitals. How can I assist you with the system today?</div>
            </div>
            <div class="input-area">
                <input type="text" id="chat-input" placeholder="Ask Dr. Jarvis to check or fix something..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        // Fetch Logs every 5 seconds
        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                const container = document.getElementById('logs-container');
                
                // Colorize errors
                const formattedLogs = data.logs.replace(/ERROR/g, '<span class="error-log">ERROR</span>')
                                               .replace(/CRITICAL/g, '<span class="error-log">CRITICAL</span>');
                
                // Only update and scroll if content changed
                if (container.innerHTML !== formattedLogs) {
                    container.innerHTML = formattedLogs || 'No logs found.';
                    container.scrollTop = container.scrollHeight;
                }
            } catch (e) {
                console.error("Failed to fetch logs");
            }
        }
        setInterval(fetchLogs, 5000);
        fetchLogs();

        // Chat functionality
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;

            // Add user message to UI
            addMessage(text, 'msg-user');
            input.value = '';

            // Loading state
            const history = document.getElementById('chat-history');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message msg-doctor';
            loadingDiv.innerText = 'Analyzing...';
            history.appendChild(loadingDiv);
            history.scrollTop = history.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await res.json();
                
                // Remove loading and add response
                history.removeChild(loadingDiv);
                addMessage(data.reply, 'msg-doctor');
            } catch (e) {
                history.removeChild(loadingDiv);
                addMessage("Connection error. The doctor is currently unreachable.", 'msg-doctor');
            }
        }

        function addMessage(text, className) {
            const history = document.getElementById('chat-history');
            const div = document.createElement('div');
            div.className = `message ${className}`;
            div.innerText = text;
            history.appendChild(div);
            history.scrollTop = history.scrollHeight;
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendMessage();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/logs')
def get_logs():
    try:
        # Read the last 50 lines of the health monitor log
        with open('/home/talha/Desktop/jartvis/health_monitor.log', 'r') as f:
            lines = f.readlines()
            return jsonify({"logs": "".join(lines[-50:])})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {e}"})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # Read the latest logs to provide to Dr. Helen
    try:
        with open('/home/talha/Desktop/jartvis/health_monitor.log', 'r') as f:
            lines = f.readlines()
            current_logs = "".join(lines[-30:])
    except:
        current_logs = "No logs available."
        
    dynamic_prompt = SYSTEM_PROMPT + f"\n\nCURRENT SYSTEM VITALS (LOGS):\n```\n{current_logs}\n```\nAnalyze these logs and take action if needed!"
    
    # Simple OpenRouter Call to act as Doctor Agent
    try:
        from dotenv import load_dotenv
        load_dotenv("/home/talha/Desktop/jartvis/.env")
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Import dynamic base URL to use 9Router proxy
        import sys
        if "/home/talha/Desktop/jartvis" not in sys.path:
            sys.path.append("/home/talha/Desktop/jartvis")
        from config import OPENROUTER_BASE_URL, OPENROUTER_MODEL
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": dynamic_prompt},
                {"role": "user", "content": user_msg}
            ]
        }
        
        res = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        reply = res_data['choices'][0]['message']['content']
        
        # Check if Dr. Helen wants to execute a command
        import re
        execute_match = re.search(r"<EXECUTE>(.*?)</EXECUTE>", reply, re.IGNORECASE | re.DOTALL)
        if execute_match:
            command = execute_match.group(1).strip()
            try:
                # Execute the command
                import subprocess
                process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                cmd_output = process.stdout + process.stderr
                reply += f"\n\n[Action Completed: Executed `{command}`]\nOutput:\n{cmd_output[:500]}"
            except Exception as e:
                reply += f"\n\n[Action Failed: Could not execute `{command}`]\nError: {e}"
                
        # Check if Dr. Helen wants to deploy an army agent
        deploy_match = re.search(r"<DEPLOY_AGENT>(.*?)\|(.*?)</DEPLOY_AGENT>", reply, re.IGNORECASE | re.DOTALL)
        if deploy_match:
            agent_name = deploy_match.group(1).strip()
            task_desc = deploy_match.group(2).strip()
            try:
                # Import the Army module and deploy
                import sys
                if "/home/talha/Desktop/jartvis" not in sys.path:
                    sys.path.append("/home/talha/Desktop/jartvis")
                from army import JarvisArmy
                army = JarvisArmy()
                army_report = army.deploy(agent_name, task_desc)
                reply += f"\n\n[Sub-Agent Deployed: {agent_name}]\nReport:\n{army_report}"
            except Exception as e:
                reply += f"\n\n[Agent Deployment Failed]\nError: {e}"
                
        # Clean up the tags for the UI so it looks nice
        reply = re.sub(r"<EXECUTE>.*?</EXECUTE>", "", reply, flags=re.IGNORECASE | re.DOTALL).strip()
        reply = re.sub(r"<DEPLOY_AGENT>.*?</DEPLOY_AGENT>", "", reply, flags=re.IGNORECASE | re.DOTALL).strip()
        
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Internal system error during diagnosis: {e}"})

if __name__ == '__main__':
    # Run Dr. Helen Dashboard on Port 8080
    app.run(host='0.0.0.0', port=8080)
