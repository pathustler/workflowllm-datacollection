import os
import re
import json
from tqdm import tqdm
from playwright.sync_api import sync_playwright

VIEWPORT = {
    "width": 2200,
    "height": 3000
}

JPEG_QUALITY = 95

def safe_name(text):
    text = re.sub(r"[^\w\s-]", "", str(text))
    return re.sub(r"\s+", "_", text.strip())

def main():
    # Load your entries
    try:
        with open("abb_marine_manuals.json") as f:
            entries = json.load(f)[:100]
    except FileNotFoundError:
        print("Error: abb_marine_manuals.json not found.")
        return

    total_saved = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        progress = tqdm(entries)

        for entry in progress:
            try:
                base_url = entry["manual_url"]
                model = safe_name(entry["model"])
                manual_title = safe_name(entry["manual_title"])

                output_dir = os.path.join("ABB_Marine_Screenshots", model)
                os.makedirs(output_dir, exist_ok=True)

                page_num = 1
                while True:
                    # Construct URL with page param
                    url = f"{base_url}?page={page_num}#manual"

                    try:
                        # Increase timeout for heavy manual pages
                        page.goto(url, wait_until="networkidle", timeout=90000)
                    except Exception:
                        break

                    # 1. Hide UI elements that might overlap the content
                    page.evaluate("""
                        () => {
                            const uiSelectors = ['.navbar', '.controlpanel', '.manual-header', '.footer', '.sidebar'];
                            uiSelectors.forEach(sel => {
                                const el = document.querySelector(sel);
                                if (el) el.style.display = 'none';
                            });
                        }
                    """)

                    # 2. Identify the specific manual content div
                    # ManualsLib typically uses .pdf or .any_page for the high-res view
                    pdf_target = page.locator(".pdf, .any_page").first

                    try:
                        # Ensure it is visible and attached
                        pdf_target.wait_for(state="visible", timeout=15000)
                        pdf_target.scroll_into_view_if_needed()
                        
                        # Short wait for lazy-loaded images inside the div to finish rendering
                        page.wait_for_timeout(3000)
                    except Exception:
                        # If we can't find the PDF div after multiple attempts, we've likely hit the end
                        break

                    # 3. Validate dimensions to prevent capturing empty containers
                    box = pdf_target.bounding_box()
                    if not box or box["width"] < 100 or box["height"] < 100:
                        break

                    image_path = os.path.join(
                        output_dir, 
                        f"{manual_title}_page_{page_num}.jpg"
                    )

                    try:
                        # Capture ONLY the specific div
                        pdf_target.screenshot(
                            path=image_path,
                            type="jpeg",
                            quality=JPEG_QUALITY,
                            animations="disabled"
                        )

                        total_saved += 1
                        progress.set_postfix({
                            "model": model[:10],
                            "page": page_num,
                            "saved": total_saved
                        })

                    except Exception as e:
                        print(f"Screenshot failed on page {page_num}: {e}")
                        break

                    page_num += 1
                    if page_num > 1000:  # Safety break
                        break

            except Exception as e:
                print(f"Error processing {entry.get('model')}: {e}")
                continue

        browser.close()

    print(f"\nDone. Total saved: {total_saved}")

if __name__ == "__main__":
    main()