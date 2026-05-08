import json
import os
from typing import List, Dict
from openai import OpenAI
from load_dotenv import load_dotenv

load_dotenv()

# -------------------------
# CONFIG
# -------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "/Users/patrickschwarz/Coding/rnaresearch/WorkflowLLM/portable_generator_workflows.json"
OUTPUT_FILE = "qa_output.json"

import re

def clean_json_output(text: str):
    # Remove markdown ```json blocks
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # Extract JSON array only
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)

    return text.strip()
# -------------------------
# BUILD CATEGORIZATIONS
# -------------------------
def build_question_categorizations(data: List[Dict]):
    categorizations = []

    for item in data:
        workflow = item.get("workflow_name", "Unknown")
        steps = item.get("steps", [])

        # Skip empty
        if not steps:
            continue

        categorizations.append({
            "category": workflow,
            "context": " ".join(steps),
            "question_types": [
                "procedural",
                "why",
                "what happens if"
            ]
        })

    return categorizations


def build_user_categorizations():
    return [
        {
            "user_type": "technician",
            "experience_level": "beginner",
            "goal": "understand device operation"
        }
    ]


# -------------------------
# CHUNKING (important)
# -------------------------
def chunk_text(text: str, size: int = 500):
    words = text.split()
    chunks = []

    for i in range(0, len(words), size):
        chunk = " ".join(words[i:i + size])
        chunks.append(chunk)

    return chunks


# -------------------------
# Q&A GENERATION
# -------------------------
def generate_qa(context: str):
    prompt = f"""
You are generating training data for a QA system.

Given the following technical content:
{context}

Generate 3-5 high-quality question-answer pairs.

Rules:
- Questions must be specific and useful
- Include procedural, reasoning, and edge-case questions
- Answers must be grounded ONLY in the text
- No hallucinations
- Keep answers concise

Return JSON:
[
  {{"question": "...", "answer": "..."}}
]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# -------------------------
# MAIN PIPELINE
# -------------------------
def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)

    question_cats = build_question_categorizations(data)

    all_qas = []

    for cat in question_cats:
        category = cat["category"]
        context = cat["context"]

        chunks = chunk_text(context)

        for chunk in chunks:
            try:
                raw_output = generate_qa(chunk)

                cleaned = clean_json_output(raw_output)

                try:
                    qas = json.loads(cleaned)
                except Exception as e:
                    print("⚠️ RAW OUTPUT:", raw_output[:500])
                    raise e

                for qa in qas:
                    qa["category"] = category
                    all_qas.append(qa)

                print(f"✅ Generated {len(qas)} QAs for: {category}")

            except Exception as e:
                print(f"❌ Error in category {category}: {e}")

    # Save output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_qas, f, indent=2)

    print(f"\n🔥 Done. Saved {len(all_qas)} QAs to {OUTPUT_FILE}")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    main()