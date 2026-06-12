import psutil
import platform
import subprocess
import json
from datetime import datetime

def get_system_info() -> str:
    """Get comprehensive system information."""
    info = {
        "os": platform.system() + " " + platform.release(),
        "hostname": platform.node(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": f"{psutil.cpu_percent()}%",
        "ram_percent": f"{psutil.virtual_memory().percent}%",
        "ram_used_gb": f"{psutil.virtual_memory().used // (1024**3):.1f}",
        "ram_total_gb": f"{psutil.virtual_memory().total // (1024**3):.1f}",
        "disk_free_gb": f"{psutil.disk_usage('/').free // (1024**3):.1f}",
        "disk_total_gb": f"{psutil.disk_usage('/').total // (1024**3):.1f}",
        "time": datetime.now().strftime("%I:%M %p"),
    }
    return str(info)

def get_active_window() -> str:
    """Get the currently active window name."""
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "Desktop"
    except Exception:
        return "Unknown"

def get_running_processes() -> str:
    """List all running processes with CPU/memory usage."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0.5 or pinfo['memory_percent'] > 0.5:
                    processes.append(f"{pinfo['name'][:30]}: CPU {pinfo['cpu_percent']:.1f}% | RAM {pinfo['memory_percent']:.1f}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return "\n".join(processes[:20])
    except Exception as e:
        return f"Error: {e}"

def get_network_info() -> str:
    """Get network information."""
    try:
        info = {}
        interfaces = psutil.net_if_addrs()
        for iface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family.name == 'AF_INET':
                    info[iface] = addr.address
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error: {e}"

def get_battery_info() -> str:
    """Get battery status if available."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery: {battery.percent}% | Plugged: {battery.power_plugged} | Remaining: {battery.secsleft//3600}h"
        return "No battery found (plugged/desktop)"
    except Exception:
        return "Battery info unavailable"

def get_disk_usage(path: str = "/") -> str:
    """Get disk usage for a specific path."""
    try:
        usage = psutil.disk_usage(path)
        return f"{path}: {usage.used // (1024**3)}GB / {usage.total // (1024**3)}GB ({usage.percent}%)"
    except Exception as e:
        return f"Error: {e}"
