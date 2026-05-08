import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

BASE = "https://www.manualslib.com"
URL = "https://www.manualslib.com/brand/abb/marine-equipment.html"


def get_soup(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def collect_manuals():
    soup = get_soup(URL)
    manuals = []
    seen = set()

    for row in soup.select("div.row.tabled"):

        model_tag = row.select_one(".mname a")
        if not model_tag:
            continue

        model = model_tag.text.strip()

        # 🔥 FIX: get ALL manual links, not just one
        for manual_tag in row.select(".mlinks a[href*='/manual/']"):

            manual_url = urljoin(BASE, manual_tag["href"]).split("#")[0]
            manual_title = manual_tag.text.strip()

            if manual_url in seen:
                continue

            seen.add(manual_url)

            manuals.append({
                "brand": "ABB",
                "product": "Marine Equipment",
                "model": model,
                "manual_title": manual_title,
                "manual_url": manual_url,
                "category": ["ABB", "Manuals Marine Equipment", model],
            })

    return manuals


if __name__ == "__main__":
    data = collect_manuals()

    with open("abb_marine_manuals.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Collected {len(data)} manuals")