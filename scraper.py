# scraper.py
import asyncio
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import (
    BrowserContext,
    async_playwright,
)
from tqdm.asyncio import tqdm_asyncio

from parser import Field, extract_form_data, goto_form, login_to_website
from utils import RateLimiter

# Load environment variables from .env file
load_dotenv()

# ------------------------------------------------------------------- #
# Configuration from environment variables
# ------------------------------------------------------------------- #
START_URL = os.getenv("START_URL", "https://app.withmascot.com/login")
MAX_PAGES = int(os.getenv("MAX_PAGES", "10"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))  # simultaneous browser tabs
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "1.0"))  # seconds between requests (same domain)

# Login Credentials
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Browser Configuration
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "/tmp/playwright-chrome-profile")
HEADLESS = os.getenv("HEADLESS", "True").lower() in ("true", "1", "yes")


# ------------------------------------------------------------------- #
async def crawl_page(
    browser: BrowserContext, url: str, limiter: RateLimiter
) -> List[Field]:
    async with limiter:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_load_state("networkidle")

            await login_to_website(USERNAME, PASSWORD, page)
            await goto_form(page)
            data = await extract_form_data(page)

            return data
        except Exception as e:
            logger.error(f"Failed {url}: {e}")
            return []
        finally:
            await page.close()


# ------------------------------------------------------------------- #
async def main() -> None:
    limiter = RateLimiter(per_second=1 / RATE_LIMIT)
    results: List[Field] = []
    # Create temp dir if needed (safe in async)
    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        # Let PWDEBUG control headless/headful
        browser = await pw.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=HEADLESS,
            args=[
                # "--remote-debugging-port=9222",
                # "--remote-debugging-address=0.0.0.0",  # Bind for host access
                "--no-sandbox",
                #     "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                #     # "--disable-features=DevToolsDebuggingRestrictions",  # Workaround for Chrome 136+ CDP restrictions (2025 issue)
            ],
        )
        # logger.info(
        #     "Browser launched. Script paused for 5 minutes. Connect to http://localhost:9222/json/list to inspect."
        # )
        # await asyncio.sleep(300)  # 5 minutes pause
        # await browser.new_context(viewport={"width": 1920, "height": 1080})
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_crawl(url):
            async with semaphore:
                return await crawl_page(browser, url, limiter)

        tasks = [bounded_crawl(START_URL)]
        for fut in tqdm_asyncio.as_completed(tasks, desc="Pages"):
            results.extend(await fut)
        await browser.close()

    # ---- export ----
    Path("output").mkdir(exist_ok=True)
    import pandas as pd

    df = pd.DataFrame([r.model_dump() for r in results])
    df.to_csv("output/mascot_fiels.csv", index=False)
    df.to_parquet("output/mascot_fields.parquet", index=False)
    logger.success(f"Saved {len(df)} records")


if __name__ == "__main__":
    asyncio.run(main())
