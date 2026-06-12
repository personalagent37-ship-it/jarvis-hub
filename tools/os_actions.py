import sys
import shutil
from datetime import datetime
import os
import subprocess

class OSActions:
    """Utility class for OS‑level actions that JARVIS can invoke.
    All methods return a short status string that will be spoken to the user.
    """
    def __init__(self):
        self.base_dir = os.getcwd()

    # ---------- Application & Process ----------
    def open_app(self, app: str) -> str:
        """Open a desktop application using the system's default method.
        Example: "firefox", "code" (VS Code), "gnome-terminal".
        """
        app = app.lower().strip()
        aliases = {
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
            "notepad": "gedit",
            "text editor": "gedit",
            "terminal": "gnome-terminal",
            "chrome": "google-chrome",
            "files": "nautilus",
            "folder": "nautilus",
            "calculator": "gnome-calculator"
        }
        actual_app = aliases.get(app, app)
        
        try:
            subprocess.Popen([actual_app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened {app}."
        except Exception as e:
            return f"Failed to open {app}: {e}"

    def run_command(self, command: str) -> str:
        """Execute an arbitrary shell command and capture its output.
        The command is run in a non‑interactive shell; output is limited to the first 200 characters.
        """
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
            out = result.stdout.strip()[:200]
            err = result.stderr.strip()[:200]
            if result.returncode == 0:
                return f"Command succeeded. Output: {out}" if out else "Command succeeded with no output."
            else:
                return f"Command failed (code {result.returncode}). Error: {err}" if err else "Command failed with no error message."
        except Exception as e:
            return f"Error executing command: {e}"

    # ---------- Package Management ----------
    def install_package(self, package: str) -> str:
        """Install a pip package into the virtual environment.
        Uses the same python interpreter that runs JARVIS.
        """
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return f"Package {package} installed successfully."
        except Exception as e:
            return f"Failed to install {package}: {e}"

    def list_packages(self) -> str:
        """List installed pip packages.
        Returns a brief comma‑separated list.
        """
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--format", "freeze"], capture_output=True, text=True, timeout=10)
            pkgs = [line.split('==')[0] for line in result.stdout.splitlines() if line]
            return f"Installed packages: {', '.join(pkgs[:20])}."
        except Exception as e:
            return f"Failed to list packages: {e}"

    # ---------- File Operations ----------
    def read_file(self, path: str) -> str:
        try:
            with open(path, 'r') as f:
                data = f.read(2000)
            return f"File content (first 2KB): {data}" if data else "File is empty."
        except Exception as e:
            return f"Could not read file {path}: {e}"

    def write_file(self, path: str, content: str) -> str:
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Wrote content to {path}."
        except Exception as e:
            return f"Failed to write to {path}: {e}"

    def append_file(self, path: str, content: str) -> str:
        try:
            with open(path, 'a') as f:
                f.write(content)
            return f"Appended content to {path}."
        except Exception as e:
            return f"Failed to append to {path}: {e}"

    def create_folder(self, path: str) -> str:
        try:
            os.makedirs(path, exist_ok=True)
            return f"Folder {path} created or already exists."
        except Exception as e:
            return f"Could not create folder {path}: {e}"

    def delete_file(self, path: str) -> str:
        try:
            os.remove(path)
            return f"File {path} deleted."
        except Exception as e:
            return f"Failed to delete file {path}: {e}"

    def copy_file(self, source: str, dest: str) -> str:
        try:
            shutil.copy2(source, dest)
            return f"Copied {source} to {dest}."
        except Exception as e:
            return f"Copy failed: {e}"

    def move_file(self, source: str, dest: str) -> str:
        try:
            shutil.move(source, dest)
            return f"Moved {source} to {dest}."
        except Exception as e:
            return f"Move failed: {e}"

    def list_files(self, path: str) -> str:
        try:
            entries = os.listdir(path)
            return f"Contents of {path}: {', '.join(entries[:30])}."
        except Exception as e:
            return f"Could not list {path}: {e}"

    def search_files(self, pattern: str, path: str) -> str:
        import fnmatch
        matches = []
        for root, dirs, files in os.walk(path):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    matches.append(os.path.join(root, name))
        if matches:
            return f"Found {len(matches)} files: {', '.join(matches[:10])}."
        return "No matching files found."

    def get_file_info(self, path: str) -> str:
        try:
            stat = os.stat(path)
            return f"Size: {stat.st_size} bytes, Modified: {datetime.fromtimestamp(stat.st_mtime)}"
        except Exception as e:
            return f"Could not retrieve info for {path}: {e}"

# End of OSActions class
