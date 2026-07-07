import os
import sys
import importlib.util
import json
import ast

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
os.makedirs(SKILLS_DIR, exist_ok=True)

def list_skills() -> str:
    """List all available self-created skills."""
    if not os.path.exists(SKILLS_DIR):
        return "No self-created skills found."
    
    skills = []
    for f in os.listdir(SKILLS_DIR):
        if f.endswith(".py") and not f.startswith("__"):
            name = f[:-3]
            path = os.path.join(SKILLS_DIR, f)
            desc = "No description"
            try:
                with open(path, "r", encoding="utf-8") as file:
                    node = ast.parse(file.read())
                    doc = ast.get_docstring(node)
                    if doc:
                        desc = doc.strip().split("\n")[0]
            except Exception:
                pass
            skills.append(f"- {name}: {desc}")
            
    if not skills:
        return "No self-created skills found."
    return "Available self-created skills:\n" + "\n".join(skills)

def create_skill(name: str, description: str, python_code: str) -> str:
    """Create and save a new skill script."""
    name = name.lower().replace(" ", "_").replace("-", "_")
    if not name.isidentifier():
        return f"Error: '{name}' is not a valid Python identifier name."
        
    path = os.path.join(SKILLS_DIR, f"{name}.py")
    
    # Ensure docstring and run method exist
    formatted_code = f'"""\n{description}\n"""\n\n' + python_code
    
    # Syntax check
    try:
        ast.parse(formatted_code)
    except SyntaxError as e:
        return f"SyntaxError in skill code: {e}"
        
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted_code)
        return f"Successfully created skill '{name}' at {path}."
    except Exception as e:
        return f"Failed to create skill '{name}': {e}"

def execute_skill(name: str, params: dict = None) -> str:
    """Execute a dynamically loaded skill."""
    params = params or {}
    name = name.lower().replace(" ", "_").replace("-", "_")
    path = os.path.join(SKILLS_DIR, f"{name}.py")
    
    if not os.path.exists(path):
        return f"Error: Skill '{name}' does not exist."
        
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, "run"):
            result = module.run(**params)
            return str(result)
        elif hasattr(module, "execute"):
            result = module.execute(**params)
            return str(result)
        else:
            return f"Error: Skill '{name}' does not have a 'run(**kwargs)' or 'execute(**kwargs)' function."
    except Exception as e:
        return f"Error executing skill '{name}': {e}"
