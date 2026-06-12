import os
import subprocess

_pyautogui = None

def _gui():
    global _pyautogui
    if _pyautogui is None:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.4
            _pyautogui = pyautogui
        except Exception as e:
            raise RuntimeError(f"GUI control is unavailable: {e}") from e
    return _pyautogui

def click(x: int, y: int, double: bool = False) -> str:
    pyautogui = _gui()
    if double:
        pyautogui.doubleClick(x, y)
    else:
        pyautogui.click(x, y)
    return f"Clicked at {x},{y}"

def type_text(text: str) -> str:
    _gui().typewrite(text, interval=0.03)
    return "Typed text"

def hotkey(keys: list) -> str:
    _gui().hotkey(*keys)
    return f"Pressed {'+'.join(keys)}"

def scroll(direction: str = "down", amount: int = 3) -> str:
    clicks = amount if direction == "up" else -amount
    _gui().scroll(clicks)
    return f"Scrolled {direction}"

def open_app(app: str) -> str:
    """Open an application using multiple strategies."""
    app_lower = app.lower().strip()
    if app.startswith("~") or app.startswith("/"):
        path = os.path.expanduser(app)
        subprocess.Popen(["xdg-open", path])
        return f"Opening {path}"
    
    # App name mappings and aliases
    app_map = {
        "whatsapp": ["flatpak", "run", "io.github.eneshecan.WhatsAppQml"],
        "discord": ["flatpak", "run", "com.discordapp.Discord"],
        "telegram": ["flatpak", "run", "org.telegram.desktop"],
        "slack": ["flatpak", "run", "com.slack.Slack"],
        "firefox": ["firefox"],
        "chrome": ["google-chrome"],
        "chromium": ["chromium"],
        "vlc": ["vlc"],
        "vscode": ["code"],
        "atom": ["atom"],
        "gedit": ["gedit"],
        "nautilus": ["nautilus"],
        "terminal": ["gnome-terminal"],
    }
    
    # Get command for app or use app name directly
    command = app_map.get(app_lower, [app_lower])
    
    # Try various strategies
    strategies = [
        command,  # Direct command
        ["xdg-open", app],  # xdg-open
        ["gtk-launch", app_lower],  # GTK launcher
        ["which", app_lower],  # Check if in PATH
    ]
    
    if app_lower == "whatsapp":
        # Also try web version as fallback
        strategies.append(["firefox", "https://web.whatsapp.com"])
    
    for attempt, strategy in enumerate(strategies):
        try:
            if strategy[0] == "which":
                # Don't execute 'which', just check if it exists
                result = subprocess.run(["which", app_lower], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    subprocess.Popen([path])
                    return f"Opening {app} from {path}"
                continue
            
            subprocess.Popen(strategy, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening {app}"
        except Exception as e:
            if attempt < len(strategies) - 1:
                continue
            return f"Could not open {app}: {str(e)[:50]}"
    
    return f"Could not find {app}"

def take_screenshot(path: str = "/tmp/jarvis_screen.png") -> str:
    """Capture a screenshot.
    Tries pyautogui first; falls back to mss if needed.
    Returns a descriptive message with the saved file path.
    """
    try:
        img = _gui().screenshot()
        img.save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        # Fallback using mss (already a dependency for vision)
        try:
            import mss
            with mss.mss() as sct:
                sct.shot(mon=0, output=path)
            return f"Screenshot (fallback) saved to {path}"
        except Exception as e2:
            return f"Failed to take screenshot: {e2}"

def get_mouse_position() -> dict:
    x, y = _gui().position()
    return {"x": x, "y": y}

def open_terminal() -> str:
    subprocess.Popen(["gnome-terminal"])
    return "Opened terminal"
