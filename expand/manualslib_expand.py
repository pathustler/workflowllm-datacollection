import json
import requests
from bs4 import BeautifulSoup
import re
import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


OUTPUT_FILE = "portable_generator_workflows.json"
CONCURRENCY = 10
SAVE_EVERY = 10

save_lock = Lock()


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
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def extract_steps_from_manual_page(url: str) -> list[str]:
    for attempt in range(5):
        try:
            r = session.get(url, timeout=30)

            if r.status_code == 200:
                break

            if r.status_code in [403, 429]:
                print(f"⚠️ Rate limited ({r.status_code}) — backing off...")
                time.sleep(2 ** attempt)
                continue

            return []

        except Exception:
            time.sleep(2 ** attempt)
    else:
        print(f"❌ Permanent failure: {url}")
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
from time import perf_counter


def main(start_index: int):

    with open("portable_generator_toc_sections.json") as f:
        toc_entries = json.load(f)

    toc_entries = toc_entries[start_index:]
    total = len(toc_entries)

    # Load checkpoint
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            workflows = json.load(f)
    else:
        workflows = []

    processed_urls = {w["source_url"] for w in workflows}

    print(f"Starting from index: {start_index}")
    print(f"Running with {CONCURRENCY} concurrent workers...\n")

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

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()

            if result:
                workflows.append(result)
                processed_urls.add(result["source_url"])
            else:
                failures += 1

            completed += 1

            # Stopwatch
            elapsed = perf_counter() - start_time
            hrs = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)

            # Progress %
            percent = (completed / total_tasks) * 100

            # Single-line overwrite
            print(
                f"\rProgress: {completed}/{total_tasks} "
                f"({percent:5.1f}%) | "
                f"Workflows: {len(workflows)} | "
                f"Failures: {failures} | "
                f"Elapsed: {hrs:02d}:{mins:02d}:{secs:02d}",
                end="",
                flush=True
            )

            # Save checkpoint
            if completed % SAVE_EVERY == 0:
                with save_lock:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(workflows, f, indent=2, ensure_ascii=False)

    # Final save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(workflows, f, indent=2, ensure_ascii=False)

    total_elapsed = perf_counter() - start_time

    print("\n\n✅ Done.")
    print(f"Total workflows: {len(workflows)}")
    print(f"Total time: {total_elapsed:.2f} seconds")



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
