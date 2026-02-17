import json
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import argparse
import os
import time


OUTPUT_FILE = "portable_generator_workflows.json"


# -----------------------------
# Utilities
# -----------------------------
def parse_style(style: str) -> dict:
    out = {}
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":")
            out[k.strip()] = v.strip().replace("px", "")
    return out


# -----------------------------
# Extraction
# -----------------------------
def extract_steps_from_manual_page(url: str) -> list[str]:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ Failed fetching {url}")
        return []

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

    blocks.sort(key=lambda b: (b["top"], b["left"]))

    steps = []
    for b in blocks:
        t = b["text"]

        if b["font"] >= 24:
            continue

        if re.match(r"^[0-9.,/]+$", t):
            continue

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


# -----------------------------
# MAIN
# -----------------------------
def main(start_index: int):
    with open("portable_generator_toc_sections.json") as f:
        toc_entries = json.load(f)

    total = len(toc_entries)

    # Load existing checkpoint if available
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            workflows = json.load(f)
        print(f"✓ Loaded {len(workflows)} existing workflows")
    else:
        workflows = []

    # Avoid duplicate processing
    processed_urls = {w["source_url"] for w in workflows}

    print(f"Starting from index: {start_index}")

    for idx in range(start_index, total):
        entry = toc_entries[idx]

        print(f"\n[{idx+1}/{total}] Processing: {entry['title']}")

        # Skip non-actionable sections
        if entry["title"].lower() in {
            "table of contents",
            "certifications and specifications",
            "certifications"
        }:
            print("→ Skipped (non-actionable)")
            continue

        # if entry["source_url"] in processed_urls:
        #     print("→ Already processed, skipping")
        #     continue

        workflow = toc_entry_to_workflow(entry)

        if workflow["steps"]:
            workflows.append(workflow)
            processed_urls.add(workflow["source_url"])

            # 🔥 Save checkpoint immediately
            with open(OUTPUT_FILE, "w") as f:
                json.dump(workflows, f, indent=2, ensure_ascii=False)

            print("✓ Checkpoint saved")
        else:
            print("→ No steps extracted")

        time.sleep(0.3)  # polite delay

    print(f"\n✅ Done. Total workflows: {len(workflows)}")


# -----------------------------
# CLI ENTRY
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start from nth TOC entry index"
    )
    args = parser.parse_args()

    main(args.start)
