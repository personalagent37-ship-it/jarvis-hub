import time
import subprocess
import os

class CyberWatcher:
    def __init__(self):
        self.running = True
        # Whitelist of safe Jarvis/System ports
        self.allowed_ports = {
            22, 53, 80, 443, 631,     # System
            3000, 5000, 8080, 20128,  # Jarvis Hub & 9Router
            8123                      # Home Assistant
        }
        print("==================================================")
        print("🛡️ COUNTER-CYBERSECURITY DAEMON ONLINE")
        print("==================================================")

    def hunt_unauthorized_ports(self):
        """Scans for unauthorized listening ports and kills the rogue process."""
        try:
            result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines[1:]: 
                if "LISTEN" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        local_address = parts[4]
                        try:
                            port = int(local_address.split(':')[-1])
                            if port not in self.allowed_ports:
                                print(f"[CYBER-DEFENSE] ⚠️ UNAUTHORIZED PORT DETECTED: {port}")
                                print(f"[CYBER-DEFENSE] 🛡️ WARNING: Port {port} is active (Assassination disabled to protect Antigravity IDE).")
                                # Kill the unauthorized process automatically (DISABLED FOR SAFETY)
                                # subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
                                self.allowed_ports.add(port) # Add to ignore list
                        except ValueError:
                            pass
        except Exception as e:
            pass

    def watch_critical_files(self):
        """Monitor .env file for unauthorized access/changes."""
        env_path = "/home/talha/Desktop/jartvis/.env"
        if os.path.exists(env_path):
            try:
                # Basic check for file permissions. If it's universally readable, lock it down.
                stat = os.stat(env_path)
                mode = oct(stat.st_mode)[-3:]
                if mode != "600":
                    print(f"[CYBER-DEFENSE] 🔒 .env file permissions are insecure ({mode}). Auto-locking to 600...")
                    os.chmod(env_path, 0o600)
            except Exception:
                pass

    def run(self):
        while self.running:
            self.watch_critical_files()
            self.hunt_unauthorized_ports()
            # Sleep for 15 seconds. Very lightweight.
            time.sleep(15)

if __name__ == "__main__":
    watcher = CyberWatcher()
    watcher.run()
