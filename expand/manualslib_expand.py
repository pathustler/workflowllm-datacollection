import json
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm


def parse_style(style: str) -> dict:
    out = {}
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":")
            out[k.strip()] = v.strip().replace("px", "")
    return out


def extract_steps_from_manual_page(url: str) -> list[str]:
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    pdf = soup.select_one("div.pdf")
    if not pdf:
        return []

    blocks = []

    for el in pdf.find_all(["div", "h2", "h3"]):
        text = el.get_text(strip=True)
        if not text:
            continue

        style = el.get("style", "")
        style_data = parse_style(style)

        blocks.append({
            "text": text,
            "top": int(style_data.get("top", 0)),
            "left": int(style_data.get("left", 0)),
            "font": int(style_data.get("font-size", 16)),
        })

    # reading order
    blocks.sort(key=lambda b: (b["top"], b["left"]))

    steps = []
    for b in blocks:
        t = b["text"]

        # skip headers / titles
        if b["font"] >= 24:
            continue

        # skip pure table data
        if re.match(r"^[0-9.,/]+$", t):
            continue

        # keep instructional / descriptive lines
        if len(t) >= 20:
            steps.append(t)

    return steps


def toc_entry_to_workflow(entry: dict) -> dict:
    steps = extract_steps_from_manual_page(entry["source_url"])

    return {
        "workflow_name": f'{entry["title"]} – {entry["manual_name"]}',
        "steps": steps,
        "source": "ManualsLib",
        "source_url": entry["source_url"]
    }


if __name__ == "__main__":
    with open("portable_generator_toc_sections.json") as f:
        toc_entries = json.load(f)

    workflows = []

    for entry in tqdm(toc_entries, desc="Extracting workflows"):
        # skip non-actionable sections early
        if entry["title"].lower() in {
            "table of contents",
            "certifications and specifications",
            "certifications"
        }:
            continue

        workflow = toc_entry_to_workflow(entry)

        if workflow["steps"]:
            workflows.append(workflow)

    with open("portable_generator_workflows.json", "w") as f:
        json.dump(workflows, f, indent=2, ensure_ascii=False)

    print(f"✓ Extracted {len(workflows)} workflows")
