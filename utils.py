# E:\Mini-JARVIS\utils.py

def log_command(command):
    with open("command_log.txt", "a") as f:
        f.write(command + "\n")
