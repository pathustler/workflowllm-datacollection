import os
import re
import json
import argparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tqdm import tqdm


OUTPUT_FILE = "portable_generator_workflows.json"
SAVE_BATCH = 500        # Save every N entries
JPEG_QUALITY = 70      # 60–75 is ideal balance
VIEWPORT = {"width": 1600, "height": 3000}

successful_screenshots = 0


# -------------------------------------------------
# Utilities
# -------------------------------------------------

def safe_name(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "_", text.strip())


def parse_style(style: str) -> dict:
    out = {}
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":")
            out[k.strip()] = v.strip().replace("px", "")
    return out


# -------------------------------------------------
# HTML → Steps Extraction (NO extra network call)
# -------------------------------------------------

def extract_steps_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
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


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main(start_index: int):

    global successful_screenshots

    with open("portable_generator_toc_sections.json") as f:
        toc_entries = json.load(f)

    toc_entries = toc_entries[start_index:]

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            workflows = json.load(f)
    else:
        workflows = []

    processed = {w["source_url"] for w in workflows}
    entries = [e for e in toc_entries if e["source_url"] not in processed]

    print(f"Processing {len(entries)} remaining pages")

    with sync_playwright() as p:

        # 🔥 SINGLE BROWSER
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = browser.new_context(viewport=VIEWPORT)

        # Allow images but block heavy junk
        context.route("**/*", lambda route, request:
            route.abort()
            if request.resource_type in ["font", "media"]
            else route.continue_()
        )

        # 🔥 SINGLE REUSED PAGE
        page = context.new_page()

        for i, entry in enumerate(tqdm(entries)):

            try:
                page.goto(entry["source_url"], wait_until="domcontentloaded")

                # Wait only for the PDF container
                page.wait_for_selector("div.pdf", timeout=15000)

                # Scroll once to trigger lazy image loads
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(300)

                html = page.content()
                steps = extract_steps_from_html(html)

                if not steps:
                    continue

                brand = safe_name(entry["brand"])
                product = safe_name(entry["product"])
                model = safe_name(entry["model"])
                manual_word = safe_name(entry["manual_name"].split()[0])
                title = safe_name(entry["title"])

                image_path = os.path.join(
                    "ManualsLib_Screenshots",
                    brand,
                    product,
                    model,
                    manual_word,
                    f"{title}.jpg"
                )

                os.makedirs(os.path.dirname(image_path), exist_ok=True)

                element = page.query_selector("div.pdf")
                if element:
                    element.screenshot(
                        path=image_path,
                        type="jpeg",
                        quality=JPEG_QUALITY
                    )
                    successful_screenshots += 1

                workflows.append({
                    "workflow_name": f'{entry["title"]} – {entry["manual_name"]}',
                    "steps": steps,
                    "manual_name": entry["manual_name"],
                    "brand": entry["brand"],
                    "product": entry["product"],
                    "model": entry["model"],
                    "manual_title": entry["manual_title"],
                    "source_url": entry["source_url"]
                })

                # 🔥 Batch save (critical for performance)
                if i % SAVE_BATCH == 0:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(workflows, f)

            except KeyboardInterrupt:
                print("\nInterrupted by user. Saving progress...")
                break
            except:
                continue

        browser.close()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(workflows, f)

    print(f"\nDone. Screenshots saved: {successful_screenshots}")


# -------------------------------------------------
# CLI
# -------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    args = parser.parse_args()

    main(args.start)