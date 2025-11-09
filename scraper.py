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
START_URL = "https://example.com/listings"
MAX_PAGES = 10
CONCURRENCY = 3  # simultaneous browser tabs
RATE_LIMIT = 1.0  # seconds between requests (same domain)


# ------------------------------------------------------------------- #
async def crawl_page(browser: Browser, url: str, limiter: RateLimiter) -> List[Listing]:
    async with limiter:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_load_state("networkidle")
            html = await page.content()
            return extract_listings(html)
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
        tasks = [
            bounded_crawl(f"{START_URL}?page={i}") for i in range(1, MAX_PAGES + 1)
        ]
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
