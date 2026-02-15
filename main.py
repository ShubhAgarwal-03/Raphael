import os
import sys
import json
import subprocess
from datetime import datetime
import uuid


from system_info import get_system_info
from rule_engine import is_allowed


try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# ======================
# CONFIG
# ======================
MODEL_NAME = "phi3:mini"
MEMORY_FILE = "memory.json"

APP_PROCESS_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "chrome": "chrome.exe"
}

# ======================
# MEMORY
# ======================

DEFAULT_MEMORY = {
    "facts": [],
    "preferences": [],
    "rules": [],
    "history": []
}



with open("app_registry.json", "r") as f:
    app_registry = json.load(f)
    # print("DEBUG FULL REGISTRY:", app_registry)




def load_memory():
    if not os.path.exists(MEMORY_FILE):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print_sys("Memory file corrupted. Resetting memory.")
            save_memory(DEFAULT_MEMORY)
            return DEFAULT_MEMORY.copy()

    # Backward compatibility / self-healing
    if not isinstance(data, dict):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    for key in DEFAULT_MEMORY:
        if key not in data or not isinstance(data[key], list):
            data[key] = []

    save_memory(data)  # normalize structure
    return data



def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

def add_memory(text, authority="high", source="user"):
    # if memory_type not in DEFAULT_MEMORY:
    #     raise ValueError("Invalid memory type")
    
    memory = load_memory()
    memory["facts"].append({
        "text": text,
        "authority": authority,
        "source": source,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    save_memory(memory)



def extract_tags(text):
    words = text.lower().split()
    return list(set([w for w in words if len(w) > 3]))


def print_sys(msg):
    print(f"Mini-JARVIS: {msg}")

# ======================
# INTENT DETECTION
# ======================
def detect_intent(text):
    t = text.lower().strip()

    if t.startswith("search memory"):
         return "search_memory"

    if "find" in t and "memory" in t:
        return "search_memory"
    
    if t.startswith("open "):
        return {
                "intent": "open_app",
                "confidence" : 0.9,
                "target": t.replace("open", "").strip(),
                "source" : "rule"
        }

    if t.startswith("close all "):
        return {
                "intent": "close_app",
                "confidence" : 0.9,
                "target": t.replace("close", "").strip()
                
        }

    if t.startswith("close "):
        # return "close_one", 0.9
        return {
                "intent": "close_app",
                "confidence" : 0.9,
                "target": text.replace("close", "").strip()
        }

    if text.startswith("remember "):
        return {
            "intent": "remember",
            "confidence": 0.85,
            "fact": text.replace("remember ", "").strip()
        }
    
    if t in ["what do you remember", "show memory"]:
        return {
            "intent": "show_memory",
            "confidence": 0.9,
            "fact": text.replace("show memory ", "").strip()
        }


    
    if t in ["what do you remember", "show memory"]:
        return "show_memory"
    
    

    if t in ["forget everything", "clear memory"]:
        return "clear_memory"

    if t in ["exit", "quit", "shutdown"]:
        return {
            "intent": "exit",
            "confidence": 1.0,
            "source": "rule"
        }

    # fallback to LLM
    llm_result = llm_detect_intent(text)
    return {
        "intent": llm_result["intent"],
        "target": llm_result.get("target"),
        "confidence": llm_result.get("confidence", 0.6),
        "source": "llm"
    }
    
    return "ask_model"

# ======================
# ACTIONS
# ======================


def open_app(command):
    app = command.replace("open ", "").strip()
    try:
        subprocess.Popen(app, shell=True)
        print_sys(f"Opened {app}.")
    except Exception as e:
        print_sys(f"Failed to open {app}: {e}")


      
def execute_command(cmd):
    try:
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.DETACHED_PROCESS )
        return True
    except Exception as e:
        print("Execution error:", e)
        return False


#--------------bg infor for open commands---------
#--------------backend notifications regarding the open commands and what heppened to them--------------------------------
def smart_open_app(app_name, os_name="windows"):
    app_name = app_name.lower()
    if app_name not in app_registry:
        print_sys(f"I don’t know how to open {app_name}.")
        return False

    cmds = app_registry[app_name].get(os_name)
    if not cmds:
        print_sys(f"{app_name} is not configured for {os_name}.")
        return False

    for cmd in cmds:
        print("Debug exec:", cmd)
        result = execute_command(cmd)
        #if result["success"]:
        if result:
            mark_command_verified(app_name, os_name)
            print_sys(f"Opened {app_name}.")
            return True
        else:
            print("Debug error:", result["stderr"])
            mark_command_failed(app_name, os_name, cmd)

    print_sys(f"All known ways to open {app_name} failed.")
    return False


# for checking the verification status of the command. 
def mark_command_verified(app, os_name):
    # app_registry[app][os_name]["verified"] = True
    pass

def mark_command_failed(app, os_name, cmd):
    cmds = app_registry[app][os_name] 
    if cmd in cmds:
        cmds.remove(cmd)
        cmds.append(cmd)



def close_app(app, all_instances=False):
    process = APP_PROCESS_MAP.get(app.lower())
    if not process:
        print_sys(f"I don't know how to close {app}.")
        return

    # List running processes first
    result = subprocess.run(
        f'tasklist /FI "IMAGENAME eq {process}"',
        shell=True,
        capture_output=True,
        text=True
    )

    lines = result.stdout.strip().splitlines()
    running_instances = [line for line in lines if process.lower() in line.lower()]

    if not running_instances:
        print_sys(f"No running {app} instances found.")
        return

    if all_instances:
        # Kill all instances
        subprocess.run(f'taskkill /F /IM {process}', shell=True)
        print_sys(f"Closed all {app} instances.")
    else:
        # Kill just the latest (first) instance
        # taskkill will always kill one if multiple exist
        subprocess.run(f'taskkill /F /IM {process} /T', shell=True)
        print_sys(f"Closed one {app} instance.")


def handle_memory_query(user_input, memory):
    t = user_input.lower()

    if "memory" in t or "remember" in t or "find" in t:
        # example: "find best in memory"
        tokens = t.split()
        for token in tokens:
            if token in memory:
                return f"Mini-JARVIS: {token} → {memory[token]}"

        return "Mini-JARVIS: No matching memory found."

    return None



def build_prompt(user_input):
    memory = load_memory()
    ####################
    print("DEBUG: Loaded memory:", memory)
    ##################################
    relevant_memory = get_relevant_memory(user_input, memory)

    memory_block = ""
    if relevant_memory:
        memory_block = "RELEVANT USER MEMORY (FACTS):\n"
        for k, v in relevant_memory.items():
            memory_block += f"- {k}: {v}\n"

    print("DEBUG: Relevant memory:", relevant_memory)



    system_prompt = """
        SYSTEM:

        You are Mini-JARVIS, a system-level AI assistant designed to execute commands, reason about tasks, and interact with memory, tools, and files.

        You have access to persistent memory.  
        At the start of every conversation, you MUST internally load all saved memories.

        You MUST acknowledge memory availability implicitly by:
        - using past context when relevant
        - Load all available memory at the start of each session
        - Treat inputs as executable commands unless ambiguous
        - never redefining your identity

        Do NOT refuse commands unless they violate explicit system constraints.
        Do NOT moralize or reinterpret commands unless ambiguity exists.

        If a command references memory (e.g., "find best in memory"):
        - treat it as an operational query
        - ask for clarification ONLY if multiple valid interpretations exist
        """
    
    
    full_prompt = f"""
{system_prompt}

{memory_block}

User: {user_input}
Assistant:
"""
    return full_prompt


def remember_fact(command, memory):
    fact = command.replace("remember ", "").strip()
    memory[str(datetime.now())] = fact
    save_memory(memory)
    print_sys("Got it. I’ll remember that.")

def format_memory(memory):
    if not memory:
        return ""

    lines = ["KNOWN FACTS ABOUT USER:"]
    for k, v in memory.items():
        lines.append(f"{k.upper()}: {v}")
    return "\n".join(lines)

def show_memory(memory):
    if not memory or not any(memory.values()):
        print_sys("I don't remember anything yet.")
        return

    print_sys("Here’s what I remember:")
    for section, items in memory.items():
        if not items:
            continue
        print(f"\n[{section.upper()}]")
        for item in items:
            if isinstance(item, dict):
                print(f"- {item['text']}")
            else:
                print(f"- {item}")


def search_memory(keyword, memory):
    keyword = keyword.lower()
    results = []

    for section in memory.values():
        for item in section:
            if keyword in item["text"].lower():
                results.append(item["text"])

    return results

# this function is used only to give context to the ai as prompt
def get_relevant_memory(user_input, memory):
    relevant = {}
    user_words = set(user_input.lower().split())

    for key, value in memory.items():
        key_words = set(key.lower().split())
        if user_words & key_words:   # intersection
            relevant[key] = value

    return relevant



def memory_to_context(limit=5):
    mem = load_memory()
    if not mem:
        return ""

    items = list(mem.items())[-limit:]  # recent memories
    context = "User memory:\n"
    for k, v in items:
        context += f"- {v}\n"

    return context

# this is used so that the system is able to get derived memory
# memory infered from repetetion, behaviour or emphasis
def derive_memory_from_text(text):
    t = text.lower()
    derived = []

    # ---------------preferences--------------------
    if any(p in t for p in ["i like", "i love", "i prefer"]):
        derived.append(("preferences", text))

    if any(p in t for p in ["i dislike", "i hate", "i avoid", "i despise", "i dont like"]):
        derived.append(("preferences", f"Dislikes: {text}"))

    # ------------------Rules----------------------    
    if "never open" in t:
        app = t.replace("never open", "").strip()
        derived.append((
    #        "rules",
            {
                "type": "block",
                "action": "open",
                "target": app
            }
        ))
    
    if "never close" in t:
        app = t.replace("never close", "").strip()
        derived.append((
            "rules",
            {
                "type": "block",
                "action":"close",
                "target": app
            }
        ))
    
    if "always open" in t:
        app = t.replace("always open", "").strip()
        derived.append((
            "rules",
            {
                "type": "enforce",
                "action": "open",
                "target": app
            }
        ))

    return derived


# setting rules from the infered data and implementing them
# defining the rule.
def add_rule(action, target):
    memory = load_memory
    memory["rules"].append({
        "type": "block",
        "action": action,
        "target": target
    })
    save_memory
    

# setting authority priority to the functions for the hierachy of system vs user vs derived commands
AUTHORITY_PRIORITY = {
    "system": 3,
    "user": 2,
    "derived": 1
}

# checking if the said action is blocked in the rules
def is_action_blocked(action, target, memory, requester="user"):
    rules = memory.get("rules", [])
    
    requester_level = AUTHORITY_PRIORITY.get(requester, 2)

    # print("DEBUG RULE CHECK:", action, target, rules)

    for rule in rules:
        
        if rule.get("type") != "block":
            continue
        if rule.get("action")!= action:
            continue
        if rule.get("target")!= target:
            continue
         
        rule_level = AUTHORITY_PRIORITY.get(rule.get("authority"), 1)
       
        if rule["authority"] == "system":
           return rule
        
        if requester == "user":
            return rule
        return None
        # only block if rule_authority > requester_authority
        # if rule_level >= requester_level:
        #     return rule

    return None
    # returns rule instead of a True/False


##--after entering input, we need to make a planner to check and then plan and then take action
def plan_action(user_input, memory):
    text = user_input.lower()

    plan = {
        "intent": "unknown",
        "confidence": 0.2,
        "blocked": False,
        "block_reason": None,
        "requires_confirmation": False,
        "clarification_needed": False,
        "clarification_question": None,
        "tools": [],
        "plan": [],
        "arguments": {}
    }

    # --- OPEN APP ---
    if text.startswith("open "):
        app = text.replace("open ", "").strip()

        # rule check
        if app in memory.get("blocked_apps", []):
            plan["intent"] = "open_app"
            plan["blocked"] = True
            plan["block_reason"] = f"Opening {app} is blocked by a rule."
            return plan

        plan.update({
            "intent": "open_app",
            "confidence": 0.9,
            "tools": ["open_app"],
            "arguments": {"app_name": app},
            "plan": [
                f"Check if {app} exists",
                f"Launch {app}"
            ]
        })
        return plan

    # --- CLOSE APP ---
    if text.startswith("close "):
        app = text.replace("close ", "").strip()
        plan.update({
            "intent": "close_app",
            "confidence": 0.9,
            "tools": ["close_app"],
            "arguments": {"app_name": app},
            "plan": [
                f"Find running process for {app}",
                f"Terminate process"
            ],
            "requires_confirmation": True
        })
        return plan

    # --- REMEMBER ---
    if text.startswith("remember "):
        fact = text.replace("remember ", "").strip()
        plan.update({
            "intent": "remember",
            "confidence": 0.85,
            "tools": ["write_memory"],
            "arguments": {"content": fact},
            "plan": ["Store information in long-term memory"]
        })
        return plan

    # --- DEFAULT ---
    plan.update({
        "intent": "ask",
        "confidence": 0.5,
        "plan": ["Answer user query conversationally"]
    })
    return plan




def clear_memory():
    print_sys("Are you sure you want to delete all memory? Enter 1 to confirm, anything else to cancel.")
    confirm = input("You: ").strip()
    if confirm == "1":
        save_memory({})
        print_sys("All memory cleared.")
    else:
        print_sys("Memory deletion canceled.")


def ask_model(prompt):
    if not OLLAMA_AVAILABLE:
        print_sys("Ollama library not installed")
        return

    try:
        # response = ollama.chat(
        #     model=MODEL_NAME,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # prompt = build_prompt(user_input)

        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt
        )
        print_sys(response["response"])
        
        # print(response["message"]["content"])
    except Exception as e:
        print_sys(f"Model error: {e}")

parsed_intent = {
    "intent": "open_app",
    "target": "chrome",
    "confidence": 0.9,
    "source": "rule"  # or "llm"
}


# ======================
# MAIN LOOP
# ======================
def main():
    print_sys("Mini-JARVIS running. Type 'exit' to quit.")
    memory = load_memory()

    while True:
        try:
            handled = False
            user_input = input("You: ").strip()
            if not user_input:
                continue

            intent_data = detect_intent(user_input)
            ############
            parsed_intent = intent_data
            intent = intent_data["intent"]
            
            print("DEBUG INTENT:", intent)
            print("DEBUG intent type:", type(intent))

            
            if intent == "exit":
                print_sys("Shutting down.")
                break

            elif intent == "open_app":
                #  app = user_input.replace("open", "").strip().lower()
                
                
                # 08-02-2026 16:08
                app = parsed_intent["target"].lower()
                blocked_rule = is_action_blocked("open", app, memory, requester="user")
                
                if blocked_rule:
                    print_sys(
                        f"Blocked by {blocked_rule['authority']} rule:"
                        f"cannot open {app}"
                    )
                    # handled = True
                    continue
                
                opened = smart_open_app(app)

                if not opened:
                    print_sys(f"Could not open {app}. You can teach me how.")
                
                continue


            elif intent == "close_one":
                app = user_input.replace("close ", "").strip()
                close_app(app, all_instances=False)
                continue

            elif intent == "close_all":
                app = user_input.replace("close all ", "").strip()
                close_app(app, all_instances=True)
                continue

            elif intent == "remember":
                content = user_input.replace("remember", "").strip()
                if not content:
                    print_sys("What should I remember?")
                    continue

                memory["facts"].append(content)
                derived_items = derive_memory_from_text(content)
                
                for item in derived_items:
                    if isinstance(item, dict):    #rule objective only
                        item["authority"] = "derived"
                        item["source"] = "inference"
                        memory["rules"].append(item)
                        
                save_memory(memory)
                print_sys("Got it. I’ll remember that.")
                continue


            elif intent == "show_memory":
                # memory = load_memory()
                show_memory(memory)
                continue


            elif intent == "search_memory":
                keyword = user_input.replace("find", "").replace("in memory", "").strip()
                #results = search_memory(keyword, memory)
                results = search_memory(keyword, memory)

                
                if not results:
                    print_sys("No matching memory found.")
                else:
                    print_sys("Here’s what I found in memory:")
                    for item in results:
                        print(f"- {item}")
                continue

                
            
            elif intent == "clear_memory":
                confirm = input("Are you sure? Enter 1 to confirm: ").strip()
                if confirm == "1":
                    memory["facts"] = []
                    save_memory(memory)
                    print_sys("Memory cleared.")
                else:
                    print_sys("Memory not cleared.")
                continue

            #if not handled:
            else:
                print("⚠️ LLM CALLED WITH:", user_input)
                ask_model(user_input)
                

        except KeyboardInterrupt:
            print_sys("Interrupted. Bye..")
            break

if __name__ == "__main__":
    main()



















