# scraper.py
import asyncio
from pathlib import Path
from typing import List

from loguru import logger
from playwright.async_api import async_playwright, Browser
from tqdm.asyncio import tqdm_asyncio

from parser import Listing, extract_listings
from utils import RateLimiter

# ------------------------------------------------------------------- #
# Configurable constants
# ------------------------------------------------------------------- #
START_URL = "https://app.withmascot.com/login"
MAX_PAGES = 10
CONCURRENCY = 1  # simultaneous browser tabs
RATE_LIMIT = 1.0  # seconds between requests (same domain)


# ------------------------------------------------------------------- #
async def crawl_page(browser: Browser, url: str, limiter: RateLimiter) -> List[Listing]:
    async with limiter:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_load_state("networkidle")

            # Interact with login form
            await page.get_by_placeholder("Enter email").fill("jhake@littleelephant.io")
            await page.get_by_placeholder("Enter password").fill("A2ADWnC34BIuOu!")
            await page.get_by_role("button", name="Sign in").click()
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
                await page.wait_for_timeout(10_000)
            except TimeoutError:
                print("Warning: Timeout while waiting after Sign In,")

            await page.screenshot(path="output/after_login.png", full_page=True)

            await page.get_by_role("button", name="Add Inventory").click()

            await page.screenshot(
                path="output/after_add_inventory_click.png", full_page=True
            )

            await page.get_by_text("Create Items Manually").click()

            await page.wait_for_timeout(3000)
            modal = page.locator("#custom-modal").first

            # Waiawait t for modal to be visible and stable
            await modal.wait_for(state="visible")
            await page.wait_for_timeout(500)  # small delay for animation (optional)

            # Now click the close button inside
            await modal.get_by_role("button", name="Close").nth(1).click(force=True)
            await page.wait_for_timeout(500)  # small delay for animation (optional)

            # click category dropbox
            await page.locator("div.css-tf8u31 div.css-1dr1o9l button").first.click(
                force=True
            )
            await page.wait_for_timeout(500)  # small delay for animation (optional)
            await page.screenshot(
                path="output/after_category_dropbox_click.png", full_page=True
            )

            # get all categories
            category_container = page.locator("div.css-jamj16")
            category_locators = category_container.locator("div.css-z6s5c0 span")
            categories = await category_locators.all_text_contents()
            cleaned_categories = [category.strip() for category in categories]
            print(cleaned_categories)

            return []
        except Exception as e:
            logger.error(f"Failed {url}: {e}")
            return []
        finally:
            await page.close()


# ------------------------------------------------------------------- #
async def main() -> None:
    limiter = RateLimiter(per_second=1 / RATE_LIMIT)
    results: List[Listing] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_crawl(url):
            async with semaphore:
                return await crawl_page(browser, url, limiter)

        # ---- simple pagination example (adapt to real site) ----
        tasks = [bounded_crawl(START_URL)]
        for fut in tqdm_asyncio.as_completed(tasks, desc="Pages"):
            results.extend(await fut)

        await browser.close()

    # ---- export ----
    Path("output").mkdir(exist_ok=True)
    import pandas as pd

    df = pd.DataFrame([r.model_dump() for r in results])
    df.to_csv("output/listings.csv", index=False)
    df.to_parquet("output/listings.parquet", index=False)
    logger.success(f"Saved {len(df)} records")


if __name__ == "__main__":
    asyncio.run(main())
