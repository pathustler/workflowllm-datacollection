import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse


BASE = "https://www.manualslib.com"



def clean_manual_base_url(url: str) -> str:
    """
    Removes fragment and query from a ManualsLib manual URL.
    """
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


def extract_toc(manual):
    html = requests.get(manual["manual_url"], timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

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
            "manual_name": f"{manual['model']} – {manual['manual_title']}"
        })

    return sections


if __name__ == "__main__":
    manuals = json.load(open("manualslib_all_manuals.json"))

    all_sections = []

    for manual in tqdm(manuals, desc="Crawling manuals"):
        sections = extract_toc(manual)
        all_sections.extend(sections)

    json.dump(
        all_sections,
        open("portable_generator_toc_sections.json", "w"),
        indent=2,
        ensure_ascii=False
    )

    print(f"✓ Extracted {len(all_sections)} TOC sections")
