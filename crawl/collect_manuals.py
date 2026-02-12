import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
from urllib.parse import urljoin

BASE = "https://www.manualslib.com"
START_URL = "https://www.manualslib.com/brand/"


def get_soup(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


# 1. collect all brand URLs
def collect_brands():
    soup = get_soup(START_URL)
    brands = []

    for row in soup.select("div.row.tabled"):
        brand_tag = row.select_one(".col1 a")
        if not brand_tag:
            continue

        brands.append({
            "brand": brand_tag.text.strip(),
            "brand_url": urljoin(BASE, brand_tag["href"])
        })

    return brands


# 2. collect product category URLs per brand
def collect_products(brand):
    soup = get_soup(brand["brand_url"])
    products = []

    for a in soup.select("div.catel a, div.cathead a"):
        href = a.get("href")
        if not href or "/brand/" not in href:
            continue

        products.append({
            "brand": brand["brand"],
            "product": a.text.strip(),
            "product_url": urljoin(BASE, href)
        })

    return products


# 3. your existing manual extraction logic (unchanged)
def collect_manuals_from_product(product):
    soup = get_soup(product["product_url"])
    manuals = []

    for row in soup.select("div.row.tabled"):
        name_tag = row.select_one(".mname a")
        manual_tag = row.select_one(".mdiv a")

        if not name_tag or not manual_tag:
            continue

        manuals.append({
            "brand": product["brand"],
            "product": product["product"],
            "model": name_tag.text.strip(),
            "manual_title": manual_tag.text.strip(),
            "manual_url": urljoin(BASE, manual_tag["href"])
        })

    return manuals


# 4. full crawl
def crawl_everything():
    all_manuals = {}
    brands = collect_brands()

    for brand in tqdm(brands, desc="Brands"):
        products = collect_products(brand)

        for product in tqdm(products, desc=f"Products ({brand['brand']})", leave=False):
            try:
                manuals = collect_manuals_from_product(product)
                for m in manuals:
                    all_manuals[m["manual_url"]] = m  # dedupe by URL
            except Exception:
                continue

    return list(all_manuals.values())


if __name__ == "__main__":
    manuals = crawl_everything()

    with open("manualslib_all_manuals.json", "w") as f:
        json.dump(manuals, f, indent=2, ensure_ascii=False)

    print(f"✓ Collected {len(manuals)} unique manuals")
