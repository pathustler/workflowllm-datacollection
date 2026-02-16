import ast

def validate(code, allowed_functions):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None)
            if name and name not in allowed_functions:
                return False

    return True