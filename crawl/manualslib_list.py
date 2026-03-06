import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse
import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE = "https://www.manualslib.com"
OUTPUT_FILE = "portable_generator_toc_sections.json"

PROXY = "http://adgkwbzb:43oaua4v9w5g@31.59.20.176:6754"

PROXIES = {
    "http": PROXY,
    "https": PROXY
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}


# -----------------------------
# URL Cleaner
# -----------------------------
def clean_manual_base_url(url: str):
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


# -----------------------------
# TOC Extraction
# -----------------------------
def extract_toc(manual):
    try:
        r = requests.get(manual["manual_url"], timeout=30, headers=HEADERS)
        r.raise_for_status()
    except Exception:
        print(f"⚠️ Failed: {manual['manual_url']}")
        return manual, []

    soup = BeautifulSoup(r.text, "html.parser")

    base_url = clean_manual_base_url(manual["manual_url"])
    sections = []

    for a in soup.select("a.ppp__caption__link"):
        title = a.get_text(strip=True)
        page = a.get("data-page")

        if not title or not page:
            continue

        sections.append({
            "title": title,
            "source_url": f"{base_url}?page={page}#manual",
            "manual_name": f"{manual['model']} – {manual['manual_title']}",
            "brand": manual["brand"],
            "product": manual["product"],
            "model": manual["model"],
            "manual_title": manual["manual_title"],
        })

    return manual, sections


# -----------------------------
# MAIN
# -----------------------------
def main(start_index: int, max_workers: int):

    manuals = json.load(open("manualslib_all_manuals.json"))
    total = len(manuals)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            all_sections = json.load(f)
        print(f"✓ Loaded {len(all_sections)} existing TOC entries")
    else:
        all_sections = []

    processed_manuals = set(
        s["manual_name"] for s in all_sections
    )

    print(f"Starting from manual index: {start_index}")

    manuals_to_process = []

    for idx in range(start_index, total):
        manual = manuals[idx]
        manual_name = f"{manual['model']} – {manual['manual_title']}"

        if manual_name in processed_manuals:
            continue

        manuals_to_process.append(manual)

    # parallel scraping
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = [executor.submit(extract_toc, m) for m in manuals_to_process]

        for future in tqdm(
        as_completed(futures),
        total=total,
        initial=start_index
                ):

            manual, sections = future.result()

            manual_name = f"{manual['model']} – {manual['manual_title']}"

            if sections:
                all_sections.extend(sections)
                processed_manuals.add(manual_name)

                with open(OUTPUT_FILE, "w") as f:
                    json.dump(all_sections, f, indent=2, ensure_ascii=False)

            time.sleep(0.1)

    print(f"\n✅ Finished. Total TOC sections: {len(all_sections)}")


# -----------------------------
# CLI ENTRY
# -----------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start from nth manual index"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Number of concurrent workers for scraping"
    )

    args = parser.parse_args()

    main(args.start)