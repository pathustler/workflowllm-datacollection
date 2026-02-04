from utils.llm import chat

def generate_query(code):
    prompt = f"""
Create a real-world user question that could be solved by the following workflow.
Do NOT mention Python or APIs.

Workflow:
{code}
"""
    return chat(prompt)
