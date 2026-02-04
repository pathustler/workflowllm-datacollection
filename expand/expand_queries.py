from utils.llm import chat

def expand_queries(api_docs, category, n=5):
    prompt = f"""
Create {n} realistic user requests in category "{category}"
that can be solved using the following APIs.

APIs:
{api_docs}

Do not mention API names.
"""
    return chat(prompt).split("\n")
