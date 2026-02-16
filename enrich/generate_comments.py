from utils.llm import chat
import json

def generate_comments(code):
    prompt = f"""
Explain each line of the following Python workflow code.

Return JSON:
{{ "line 1": "...", "line 2": "..." }}

Code:
{code}
"""
    return json.loads(chat(prompt))
