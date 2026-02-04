from utils.llm import chat

def generate_plan(code, comments):
    prompt = f"""
Based on the workflow and comments below, write a step-by-step task plan.

Comments:
{comments}

Code:
{code}
"""
    return chat(prompt)
