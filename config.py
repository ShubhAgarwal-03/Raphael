# E:\Mini-JARVIS\config.py
import os
import json

# Paths for Ollama local model
OLLAMA_HOME = os.getenv("OLLAMA_HOME", "E:\\Ollama\\OllamaModels")
OLLAMA_CACHE = os.getenv("OLLAMA_CACHE", "E:\\Ollama\\OllamaCache")

# Model name (replace with the model you will use)
MODEL_NAME = "llama2-7b-chat"


with open("app_registry.json") as f:
    app_registry = json.load(f)
    

def find_app_by_capability(capability: str):
    for app, data in app_registry.items():
        caps = data.get("capabilities", [])
        if capability in caps:
            return app
    return None
