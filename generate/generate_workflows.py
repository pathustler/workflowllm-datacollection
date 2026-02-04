from utils.llm import chat

def generate_workflows(query, api_docs):
    prompt = f"""
            You are a workflow engine.

            Query:
            {query}

            Allowed APIs:
            {api_docs}

            Return:
            Thought:
            (step-by-step plan)

            Code:
            ```python
            <workflow code>
            ```
            """
    return chat(prompt)
