import subprocess
import os

def shutdown(delay: int = 0) -> str:
    """Schedule system shutdown."""
    try:
        if delay > 0:
            result = subprocess.run(
                ["shutdown", "-h", f"+{delay}"],
                capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                ["shutdown", "-h", "now"],
                capture_output=True, text=True, timeout=5
            )
        return f"Shutdown scheduled in {delay} minutes" if delay > 0 else "Shutting down now"
    except Exception as e:
        return f"Error: {e}"

def reboot(delay: int = 0) -> str:
    """Schedule system reboot."""
    try:
        if delay > 0:
            result = subprocess.run(
                ["shutdown", "-r", f"+{delay}"],
                capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                ["shutdown", "-r", "now"],
                capture_output=True, text=True, timeout=5
            )
        return f"Reboot scheduled in {delay} minutes" if delay > 0 else "Rebooting now"
    except Exception as e:
        return f"Error: {e}"

def lock_screen() -> str:
    """Lock the screen."""
    try:
        subprocess.run(["gnome-screensaver-command", "-l"], timeout=5)
        return "Screen locked"
    except:
        try:
            subprocess.run(["loginctl", "lock-session"], timeout=5)
            return "Screen locked"
        except Exception as e:
            return f"Error: {e}"

def unlock_screen(password: str = None) -> str:
    """Unlock the screen."""
    try:
        # Try loginctl first which usually doesn't need the password
        subprocess.run(["loginctl", "unlock-session"], timeout=5)
        
        # If password is provided, try typing it in case GNOME requires it
        if password:
            import time
            try:
                # Wake up the screen
                subprocess.run(["xdotool", "mousemove_relative", "1", "1"], timeout=2, env=os.environ)
                time.sleep(0.5)
                # Hit escape to clear screen saver
                subprocess.run(["xdotool", "key", "Escape"], timeout=2, env=os.environ)
                time.sleep(1)
                # Type password and hit enter
                subprocess.run(["xdotool", "type", password], timeout=2, env=os.environ)
                subprocess.run(["xdotool", "key", "Return"], timeout=2, env=os.environ)
            except:
                pass
                
        return "Screen unlocked"
    except Exception as e:
        return f"Error: {e}"

def suspend() -> str:
    """Suspend the system."""
    try:
        subprocess.run(["systemctl", "suspend"], timeout=5)
        return "System suspended"
    except Exception as e:
        return f"Error: {e}"

def get_running_services() -> str:
    """List running systemd services."""
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=running"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.split('\n')
        return "\n".join(lines[:20])
    except Exception as e:
        return f"Error: {e}"

def start_service(service: str) -> str:
    """Start a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "start", service],
            capture_output=True, text=True, timeout=10
        )
        return f"Started {service}"
    except Exception as e:
        return f"Error: {e}"

def stop_service(service: str) -> str:
    """Stop a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "stop", service],
            capture_output=True, text=True, timeout=10
        )
        return f"Stopped {service}"
    except Exception as e:
        return f"Error: {e}"

def restart_service(service: str) -> str:
    """Restart a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "restart", service],
            capture_output=True, text=True, timeout=10
        )
        return f"Restarted {service}"
    except Exception as e:
        return f"Error: {e}"

def kill_process(pid: int) -> str:
    """Kill a process by PID."""
    try:
        os.kill(pid, 9)
        return f"Killed process {pid}"
    except Exception as e:
        return f"Error: {e}"

def get_environment_variables() -> str:
    """Get all environment variables."""
    try:
        return "\n".join([f"{k}={v}" for k, v in os.environ.items()][:30])
    except Exception as e:
        return f"Error: {e}"

def set_environment_variable(key: str, value: str) -> str:
    """Set environment variable for current session."""
    try:
        os.environ[key] = value
        return f"Set {key}={value}"
    except Exception as e:
        return f"Error: {e}"

def clear_clipboard() -> str:
    """Clear system clipboard."""
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-i"],
            input=b"",
            timeout=5
        )
        return "Clipboard cleared"
    except:
        try:
            subprocess.run(
                ["xsel", "-b", "-c"],
                timeout=5
            )
            return "Clipboard cleared"
        except Exception as e:
            return f"Error: {e}"

def get_clipboard() -> str:
    """Get system clipboard content."""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout[:500]
    except:
        try:
            result = subprocess.run(
                ["xsel", "-b"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout[:500]
        except Exception as e:
            return f"Error: {e}"
