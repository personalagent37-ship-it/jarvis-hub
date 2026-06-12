import os
import shutil
import glob
import json
from pathlib import Path
from datetime import datetime

def read(path: str) -> str:
    """Read file contents."""
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as f:
            return f.read()[:5000]
    except Exception as e:
        return f"Error reading file: {e}"

def write(path: str, content: str) -> str:
    """Write content to file."""
    try:
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def append(path: str, content: str) -> str:
    """Append content to file."""
    try:
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Appended to {path}"
    except Exception as e:
        return f"Error: {e}"

def create_folder(path: str) -> str:
    """Create a directory."""
    try:
        os.makedirs(os.path.expanduser(path), exist_ok=True)
        return f"Created folder: {path}"
    except Exception as e:
        return f"Error: {e}"

def list_files(path: str = "~") -> str:
    """List files in directory."""
    try:
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            return f"Not a directory: {path}"
        files = os.listdir(path)
        return "\n".join(files[:50])
    except Exception as e:
        return f"Error: {e}"

def delete(path: str) -> str:
    """Delete file or directory."""
    try:
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Deleted directory: {path}"
        return f"Path not found: {path}"
    except Exception as e:
        return f"Error: {e}"

def copy(source: str, dest: str) -> str:
    """Copy file or directory."""
    try:
        source = os.path.expanduser(source)
        dest = os.path.expanduser(dest)
        if os.path.isfile(source):
            shutil.copy2(source, dest)
            return f"Copied {source} to {dest}"
        elif os.path.isdir(source):
            shutil.copytree(source, dest)
            return f"Copied directory {source} to {dest}"
        return f"Source not found: {source}"
    except Exception as e:
        return f"Error: {e}"

def move(source: str, dest: str) -> str:
    """Move file or directory."""
    try:
        source = os.path.expanduser(source)
        dest = os.path.expanduser(dest)
        shutil.move(source, dest)
        return f"Moved {source} to {dest}"
    except Exception as e:
        return f"Error: {e}"

def search_files(pattern: str, path: str = "~") -> str:
    """Search for files matching pattern."""
    try:
        path = os.path.expanduser(path)
        matches = glob.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        return "\n".join(matches[:30])
    except Exception as e:
        return f"Error: {e}"

def get_file_info(path: str) -> str:
    """Get detailed file information."""
    try:
        path = os.path.expanduser(path)
        stat = os.stat(path)
        info = {
            "path": path,
            "size_bytes": stat.st_size,
            "size_mb": f"{stat.st_size / (1024**2):.2f}",
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "permissions": oct(stat.st_mode)[-3:],
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error: {e}"

def set_permissions(path: str, mode: str) -> str:
    """Set file permissions (mode like 755)."""
    try:
        path = os.path.expanduser(path)
        os.chmod(path, int(mode, 8))
        return f"Set permissions {mode} on {path}"
    except Exception as e:
        return f"Error: {e}"
