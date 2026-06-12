import subprocess
import tempfile
import os
import sys

def run_command(command: str, timeout: int = 30, cwd: str = None) -> str:
    """Execute shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser(cwd) if cwd else None,
        )
        output = result.stdout + result.stderr
        return output[:2000] if output else "Command completed"
    except subprocess.TimeoutExpired:
        return f"Command timed out (>{timeout}s)"
    except Exception as e:
        return f"Error: {e}"

def run_python(code: str, timeout: int = 30) -> str:
    """Execute Python code."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        tmpfile = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmpfile],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        return (result.stdout + result.stderr)[:2000]
    except subprocess.TimeoutExpired:
        return f"Python execution timed out (>{timeout}s)"
    except Exception as e:
        return f"Error: {e}"
    finally:
        try:
            os.remove(tmpfile)
        except:
            pass

def install_package(package: str) -> str:
    """Install Python package via pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return f"Installed {package}"
        return f"Failed to install {package}: {result.stderr[:500]}"
    except Exception as e:
        return f"Error: {e}"

def uninstall_package(package: str) -> str:
    """Uninstall Python package via pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "--quiet", package],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return f"Uninstalled {package}"
        return f"Failed to uninstall {package}"
    except Exception as e:
        return f"Error: {e}"

def list_packages() -> str:
    """List installed Python packages."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[:2000]
    except Exception as e:
        return f"Error: {e}"

def run_script(script_path: str, args: str = "") -> str:
    """Execute a Python script file."""
    try:
        script_path = os.path.expanduser(script_path)
        result = subprocess.run(
            [sys.executable, script_path] + (args.split() if args else []),
            capture_output=True, text=True, timeout=60
        )
        return (result.stdout + result.stderr)[:2000]
    except Exception as e:
        return f"Error: {e}"
