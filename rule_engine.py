# rule_engine.py

def is_allowed(intent: str, target: str, derived_rules: list) -> bool:
    for rule_type, rule in derived_rules:
        if (
            rule["type"] == "block"
            and rule["action"] == intent
            and rule["target"] == target
        ):
            return False
    return True
