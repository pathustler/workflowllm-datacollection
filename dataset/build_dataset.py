import json

def build_dataset(query, plan, code, api_docs):
    return {
        "query": query,
        "plan": plan,
        "code": code,
        "api_docs": api_docs
    }

dataset = []
# append validated samples
json.dump(dataset, open("workflow_dataset.json", "w"), indent=2)
