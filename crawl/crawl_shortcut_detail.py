from playwright.sync_api import sync_playwright, TimeoutError
import json
import time
from pathlib import Path

BASE = "https://routinehub.co"


def crawl_shortcut_details(shortcuts, sleep=1):
    enriched = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        for idx, sc in enumerate(shortcuts):
            url = sc["url"]
            print(f"[{idx+1}/{len(shortcuts)}] Visiting {url}")

            try:
                page.goto(url, timeout=45000)
                # ✅ wait for ANY stable element on detail page
                page.wait_for_selector("h1, .content, body", timeout=15000)
            except TimeoutError:
                print("    ⚠️ Page load timeout — skipping")
                continue

            # ---------- Title ----------
            title_el = page.query_selector("h1")
            title = title_el.inner_text().strip() if title_el else sc["title"]

            # ---------- Long description ----------
            desc_el = page.query_selector(".content")
            long_desc = (
                desc_el.inner_text().strip()
                if desc_el
                else sc.get("description", "")
            )

            # ---------- Categories ----------
            categories = []
            for el in page.query_selector_all(".categories svg title"):
                categories.append(el.inner_text().strip())

            # ---------- iCloud URL ----------
            icloud_url = None
            for a in page.query_selector_all("a"):
                href = a.get_attribute("href")
                if href and "icloud.com/shortcuts/" in href:
                    icloud_url = href
                    break

            print(
                f"    → categories={categories or '∅'} | icloud_url={'YES' if icloud_url else 'NO'}"
            )

            enriched.append({
                "title": title,
                "short_description": sc.get("description", ""),
                "long_description": long_desc,
                "categories": categories,
                "routinehub_url": url,
                "icloud_url": icloud_url,
            })

            time.sleep(sleep)

        browser.close()

    return enriched


if __name__ == "__main__":
    input_path = Path("raw_shortcuts.json")
    output_path = Path("shortcuts_enriched.json")

    shortcuts = json.load(open(input_path))
    enriched = crawl_shortcut_details(shortcuts)

    json.dump(enriched, open(output_path, "w"), indent=2, ensure_ascii=False)

    print(f"\n[✓] Saved {len(enriched)} shortcuts to {output_path}")
