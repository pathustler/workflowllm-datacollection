import asyncio
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def screenshot_pdf_div(url: str, output_path: str):
    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,  # change to False if you want to see the browser
            args=["--no-sandbox"]
        )

        context = await browser.new_context(
            viewport={"width": 1600, "height": 3000}
        )

        page = await context.new_page()

        print(f"Opening: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except PlaywrightTimeoutError:
            print("❌ Page load timeout")
            await browser.close()
            return

        try:
            # Wait for the div.pdf to appear
            await page.wait_for_selector("div.pdf", timeout=30000)
        except PlaywrightTimeoutError:
            print("❌ div.pdf not found")
            await browser.close()
            return

        element = await page.query_selector("div.pdf")

        if not element:
            print("❌ Could not select div.pdf")
            await browser.close()
            return

        # Scroll element into view (important sometimes)
        await element.scroll_into_view_if_needed()

        # Take screenshot
        await element.screenshot(
            path=output_path,
            type="png"
        )

        print(f"✅ Saved screenshot: {output_path}")

        await browser.close()


# ==============================
# RUN
# ==============================

if __name__ == "__main__":

    test_url = "https://www.manualslib.com/manual/1184180/Marine-10-M.html?page=5#manual"

    output_file = os.path.join(OUTPUT_DIR, "page.png")

    asyncio.run(
        screenshot_pdf_div(test_url, output_file)
    )