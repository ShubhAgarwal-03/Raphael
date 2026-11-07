import re

def extract_expression(text: str):
    match = re.search(r'([0-9\.\+\-\*/\(\) ]+)', text)
    if match:
        return match.group(1).strip()
    return None


def safe_calculate(expr: str):
    try:
        # VERY basic safety filter
        if not all(c in "0123456789+-*/(). " for c in expr):
            return None

        result = eval(expr)
        return f"{expr} = {result}"
    except:
        return None
