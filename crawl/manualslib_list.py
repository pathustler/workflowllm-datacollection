import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse
import argparse
import os
import time


BASE = "https://www.manualslib.com"
OUTPUT_FILE = "portable_generator_toc_sections.json"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "en-US,en;q=0.9"
}


# -----------------------------
# Shared Session
# -----------------------------
session = requests.Session()
session.headers.update(HEADERS)

# establish cookies
try:
    session.get(BASE, timeout=30)
except:
    pass


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

    url = clean_manual_base_url(manual["manual_url"])

    for attempt in range(3):

        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()

            # Sometimes ManualsLib returns placeholder pages
            if "ppp__caption__link" not in r.text:
                return []

            break

        except Exception:

            if attempt == 2:
                print(f"⚠️ Failed: {url}")
                return []

            time.sleep(2 ** attempt)

    soup = BeautifulSoup(r.text, "html.parser")

    sections = []

    for a in soup.select("a.ppp__caption__link"):

        title = a.get_text(strip=True)
        page = a.get("data-page")

        if not title or not page:
            continue

        sections.append({
            "title": title,
            "source_url": f"{url}?page={page}#manual",
            "manual_name": f"{manual['model']} – {manual['manual_title']}",
            "brand": manual["brand"],
            "product": manual["product"],
            "model": manual["model"],
            "manual_title": manual["manual_title"],
        })

    return sections


# -----------------------------
# MAIN
# -----------------------------
def main(start_index: int):

    manuals = json.load(open("manualslib_all_manuals.json"))
    total = len(manuals)

    processed_manuals = set()

    if os.path.exists(OUTPUT_FILE):

        with open(OUTPUT_FILE) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    processed_manuals.add(obj["manual_name"])
                except:
                    pass

    print(f"Starting from manual index: {start_index}")

    for idx in tqdm(range(start_index, total), total=total, initial=start_index):

        manual = manuals[idx]
        manual_name = f"{manual['model']} – {manual['manual_title']}"

        if manual_name in processed_manuals:
            continue

        sections = extract_toc(manual)

        if sections:

            with open(OUTPUT_FILE, "a") as f:

                for s in sections:
                    f.write(json.dumps(s, ensure_ascii=False) + ",\n")

        # polite delay
        time.sleep(1)


    print("Finished.")


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

    args = parser.parse_args()

    main(args.start)