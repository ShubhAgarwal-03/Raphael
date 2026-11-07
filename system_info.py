# system_info.py
import platform

def get_system_info():
    return {
        "os": platform.system().lower(),
        "release": platform.release(),
        "machine": platform.machine()
    }
