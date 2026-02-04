from playwright.sync_api import sync_playwright
import json

BASE = "https://routinehub.co"

def crawl_shortcuts(limit=30):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{BASE}/shortcuts", timeout=60000)
        page.wait_for_load_state("networkidle")

        cards = page.query_selector_all(".shortcut-card")
        print(f"[+] Found {len(cards)} shortcut cards")

        for card in cards:
            if len(results) >= limit:
                break

            # title + description
            title_el = card.query_selector("strong")
            desc_el = card.query_selector("small")

            # URL is on parent <a>
            link_el = card.evaluate_handle("el => el.closest('a')")

            if not title_el or not link_el:
                continue

            title = title_el.inner_text().strip()
            desc = desc_el.inner_text().strip() if desc_el else ""
            href = link_el.get_property("href").json_value()

            results.append({
                "title": title,
                "description": desc,
                "url": href,
            })

            print(f"  → {title}")

        browser.close()

    return results


if __name__ == "__main__":
    data = crawl_shortcuts(30)

    print(f"[✓] Collected {len(data)} shortcuts")

    with open("raw_shortcuts.json", "w") as f:
        json.dump(data, f, indent=2)

    print("[✓] Saved raw_shortcuts.json")
