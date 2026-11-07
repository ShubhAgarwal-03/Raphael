# executor.py
import subprocess

def execute_command(cmd: list[str]) -> dict:
    try:
        subprocess.Popen(cmd)
        return {"success": True}
    except Exception as e:
        return {"success": False, "stderr": str(e)}

