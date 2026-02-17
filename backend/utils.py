"""
Utility functions for code execution and file management
"""
import os
import sys
import subprocess
from typing import Tuple


def ensure_generated_dir(base_path: str = "generated") -> str:
    """Ensure the generated directory exists and return its path"""
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    return base_path


def execute_generated_code(code_string: str, filename: str = "temp_diagram_script.py") -> Tuple[bool, str]:
    """
    Writes the string to a python file and executes it.
    Returns: (success: bool, output: str)
    """
    generated_dir = ensure_generated_dir()
    filepath = os.path.join(generated_dir, filename)
    
    with open(filepath, "w") as f:
        f.write(code_string)
    
    try:
        # Set up environment with expanded PATH for graphviz2drawio
        env = os.environ.copy()
        home_dir = os.path.expanduser("~")
        local_bin = os.path.join(home_dir, ".local", "bin")
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
        
        # Run the script in a subprocess
        # cwd="generated" ensures the image is saved in that folder
        result = subprocess.run(
            [sys.executable, filename],
            cwd=generated_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,  # 2 minute timeout
            env=env  # Use modified environment
        )
        return True, "Success"
    except subprocess.CalledProcessError as e:
        # Return the error message (Traceback)
        return False, e.stderr
    except subprocess.TimeoutExpired:
        return False, "Code execution timed out after 120 seconds"



def get_latest_files(base_filename: str, generated_dir: str = "generated") -> dict:
    """
    Get the paths to generated files for a given base filename.
    Returns dict with format -> filepath mappings.
    """
    files = {}
    extensions = ["png", "dot", "drawio"]
    
    for ext in extensions:
        filepath = os.path.join(generated_dir, f"{base_filename}.{ext}")
        if os.path.exists(filepath):
            files[ext] = filepath
    
    return files


def read_drawio_xml(filepath: str) -> str:
    """Read and return the content of a .drawio file"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def save_drawio_xml(filepath: str, xml_content: str) -> bool:
    """Save Draw.IO XML content to a file"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return True
    except Exception as e:
        print(f"Error saving drawio file: {e}")
        return False


def cleanup_old_files(session_id: str, generated_dir: str = "generated"):
    """Clean up old generated files for a session"""
    import glob
    pattern = os.path.join(generated_dir, f"{session_id}*")
    for filepath in glob.glob(pattern):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error cleaning up {filepath}: {e}")
