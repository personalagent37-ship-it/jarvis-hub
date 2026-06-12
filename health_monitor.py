import time
import requests
import subprocess
import datetime
import os

LOG_FILE = "/home/talha/Desktop/jartvis/health_monitor.log"

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}\n"
    print(formatted.strip())
    try:
        with open(LOG_FILE, "a") as f:
            f.write(formatted)
    except:
        pass

def check_service(url, name, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True
        log(f"WARNING: {name} returned status code {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        log(f"ERROR: {name} is unreachable. Exception: {e}")
        return False

def restart_jarvis():
    log("CRITICAL ERROR DETECTED. RESTARTING JARVIS HUB SERVICE...")
    try:
        subprocess.run(["systemctl", "--user", "restart", "jarvis-hub.service"], check=True)
        log("SUCCESS: jarvis-hub.service restarted successfully. Giving it 60 seconds to boot.")
        time.sleep(60)
    except Exception as e:
        log(f"FAILED to restart jarvis-hub.service: {e}")

def main():
    log("=========================================")
    log(" JARVIS 24/7 HEALTH MONITOR ONLINE")
    log("=========================================")
    
    # Give the system 60 seconds to fully boot before starting checks
    time.sleep(60)
    
    consecutive_failures = 0
    
    while True:
        try:
            # 1. Check Node.js WhatsApp Hub
            hub_healthy = check_service("http://localhost:3000/api/status", "Node.js WhatsApp Hub", timeout=5)
            
            # 2. Check 9Router Next.js Server
            router_healthy = check_service("http://localhost:20128/api/v1/models", "9Router Proxy", timeout=15)
            
            if hub_healthy and router_healthy:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                log(f"Service check failed. Consecutive failures: {consecutive_failures}/3")
                
            if consecutive_failures >= 3:
                # 3 strikes and you're out. Restart the entire system.
                restart_jarvis()
                consecutive_failures = 0
                
        except Exception as e:
            log(f"Unexpected error in health monitor loop: {e}")
            
        time.sleep(30)

if __name__ == "__main__":
    main()
