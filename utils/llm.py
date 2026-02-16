import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat(prompt, model="gpt-4o-mini", temperature=0.3):
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message["content"]
