import os
import re
import json
import argparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tqdm import tqdm


OUTPUT_FILE = "marine_workflows.json"
SAVE_BATCH = 200
VIEWPORT = {"width": 1600, "height": 3000}


# -------------------------------------------------
# UTILITIES
# -------------------------------------------------

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_goto(page, url, retries=3):
    for attempt in range(retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return True
        except Exception:
            print(f"Retry {attempt+1} → {url}")
            page.wait_for_timeout(1000 * (attempt + 1))

    print(f"❌ Failed permanently: {url}")
    return False


# -------------------------------------------------
# EXTRACTION
# -------------------------------------------------

def extract_steps_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # 1. PDF-style
    pdf = soup.select_one("div.pdf")
    if pdf:
        blocks = []

        for el in pdf.find_all(["div", "h2", "h3"]):
            text = clean_text(el.get_text())
            if not text:
                continue

            style = el.get("style", "")
            if "top" in style:
                blocks.append(text)

        if blocks:
            return [b for b in blocks if len(b) > 20]

    # 2. HTML manual
    content = soup.select_one("#manual-content")
    if content:
        steps = []

        for el in content.find_all(["p", "li", "td"]):
            text = clean_text(el.get_text())

            if not text:
                continue
            if len(text) < 30:
                continue
            if re.match(r"^[0-9.,/]+$", text):
                continue

            steps.append(text)

        return steps

    # 3. fallback
    steps = []
    for el in soup.find_all(["p", "li"]):
        text = clean_text(el.get_text())
        if len(text) > 30:
            steps.append(text)

    return steps


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main(start_index: int):

    with open("abb_marine_manuals.json") as f:
        entries = json.load(f)

    entries = entries[start_index:]

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            workflows = json.load(f)
    else:
        workflows = []

    processed = {w["manual_url"] for w in workflows if "manual_url" in w}
    entries = [e for e in entries if e["manual_url"] not in processed]

    print(f"Processing {len(entries)} manuals")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-http2",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            viewport=VIEWPORT,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # block heavy stuff
        context.route("**/*", lambda route, request:
            route.abort()
            if request.resource_type in ["font", "media"]
            else route.continue_()
        )

        page = context.new_page()

        for i, entry in enumerate(tqdm(entries)):

            try:
                base_url = entry["manual_url"]

                page_num = 1
                all_steps = []

                while True:
                    url = f"{base_url}?page={page_num}"

                    if not safe_goto(page, url):
                        break

                    page.wait_for_timeout(800)

                    html = page.content()

                    # stop condition
                    if "Page Not Found" in html or "404" in html:
                        break

                    steps = extract_steps_from_html(html)

                    if not steps:
                        break

                    all_steps.extend(steps)

                    print(f"{entry['model']} page {page_num}: {len(steps)} steps")

                    page_num += 1

                    # prevent infinite loops
                    if page_num > 300:
                        break

                    # slow down slightly (prevents blocking)
                    page.wait_for_timeout(500)

                if not all_steps:
                    continue

                manual_name = f'{entry["model"]} – {entry["manual_title"]}'

                workflows.append({
                    "workflow_name": manual_name,
                    "steps": all_steps,
                    "manual_name": manual_name,
                    "category": entry.get("category", ["unknown", "unknown"]),
                    "model": entry["model"],
                    "manual_title": entry["manual_title"],
                    "manual_url": entry["manual_url"]
                })

                if i % SAVE_BATCH == 0:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(workflows, f, indent=2)

            except KeyboardInterrupt:
                print("\nInterrupted. Saving...")
                break
            except Exception as e:
                print("Error:", e)
                continue

        browser.close()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(workflows, f, indent=2)

    print("\nDone.")


# -------------------------------------------------
# CLI
# -------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()

    main(args.start)