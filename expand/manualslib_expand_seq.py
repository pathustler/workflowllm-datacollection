import json
import requests
from bs4 import BeautifulSoup
import re
import argparse
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import perf_counter


OUTPUT_FILE = "portable_generator_workflows.json"
CONCURRENCY = 4  # lower for HPC stability
SAVE_EVERY = 10

save_lock = Lock()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}


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

    for attempt in range(5):

        # jitter delay (important)
        time.sleep(random.uniform(0.3, 1.0))

        try:
            r = requests.get(url, headers=HEADERS, timeout=30)

            if r.status_code == 200:
                break

            if r.status_code in [403, 429, 503]:
                # exponential backoff
                time.sleep(3 * (attempt + 1))
                continue

            return []

        except Exception:
            time.sleep(2 ** attempt)

    else:
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


def process_entry(entry):

    if entry["title"].lower() in {
        "table of contents",
        "certifications and specifications",
        "certifications"
    }:
        return None

    steps = extract_steps_from_manual_page(entry["source_url"])

    if not steps:
        return None

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

    toc_entries = toc_entries[start_index:]

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            workflows = json.load(f)
    else:
        workflows = []

    processed_urls = {w["source_url"] for w in workflows}

    print(f"Starting from index: {start_index}")
    print(f"Running with {CONCURRENCY} workers...\n")

    start_time = perf_counter()

    completed = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:

        futures = [
            executor.submit(process_entry, entry)
            for entry in toc_entries
            if entry["source_url"] not in processed_urls
        ]

        total_tasks = len(futures)

        for future in as_completed(futures):
            result = future.result()

            if result:
                workflows.append(result)
                processed_urls.add(result["source_url"])
            else:
                failures += 1

            completed += 1

            elapsed = perf_counter() - start_time
            hrs = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)

            percent = (completed / total_tasks) * 100

            print(
                f"\rProgress: {completed}/{total_tasks} "
                f"({percent:5.1f}%) | "
                f"Workflows: {len(workflows)} | "
                f"Failures: {failures} | "
                f"Elapsed: {hrs:02d}:{mins:02d}:{secs:02d}",
                end="",
                flush=True
            )

            if completed % SAVE_EVERY == 0:
                with save_lock:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(workflows, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(workflows, f, indent=2, ensure_ascii=False)

    print("\n\n✅ Done.")
    print(f"Total workflows: {len(workflows)}")


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
