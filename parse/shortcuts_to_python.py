def shortcut_to_python(actions):
    """
    actions: list of dicts parsed from shortcut plist
    """
    code = []
    indent = 0

    for a in actions:
        if a["type"] == "if_start":
            code.append("    " * indent + f"if {a['condition']}:")
            indent += 1

        elif a["type"] == "if_end":
            indent -= 1

        elif a["type"] == "loop":
            code.append("    " * indent + f"for _ in range({a['count']}):")
            indent += 1

        else:
            code.append("    " * indent + f"{a['call']}")

    return "\n".join(code)
