# E:\Mini-JARVIS\commands.py
import os
import subprocess

def open_notepad():
    os.system("notepad.exe")

def open_calculator():
    os.system("calc.exe")

def open_browser():
    subprocess.run(["start", "chrome"], shell=True)

# Minimal system action mapping
COMMANDS_MAP = {
    "open notepad": open_notepad,
    "open calculator": open_calculator,
    "open browser": open_browser
}
