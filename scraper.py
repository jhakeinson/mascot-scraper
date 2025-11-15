# scraper.py
import asyncio
from pathlib import Path
from typing import List

from loguru import logger
from pandas._libs.lib import count_level_2d
from playwright.async_api import Locator, Page, async_playwright, Browser
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


async def login_to_website(page):
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


async def goto_form(page):
    await page.get_by_role("button", name="Add Inventory").click()

    await page.screenshot(path="output/after_add_inventory_click.png", full_page=True)

    await page.get_by_text("Create Items Manually").click()

    await page.wait_for_timeout(3000)
    modal = page.locator("#custom-modal").first

    # Wait for modal to be visible and stable
    await modal.wait_for(state="visible")
    await page.wait_for_timeout(500)  # small delay for animation (optional)

    # Now click the close button inside
    await modal.get_by_role("button", name="Close").nth(1).click(force=True)
    await page.wait_for_timeout(500)  # small delay for animation (optional)


async def get_all_category_locatora(
    category_dropdown_selector, page: Page
) -> List[Locator]:
    category_dropdown_locator = page.locator(category_dropdown_selector).first
    await category_dropdown_locator.click(force=True)
    await page.wait_for_timeout(500)  # small delay for animation (optional)
    await page.screenshot(
        path="output/after_category_dropbox_click.png", full_page=True
    )

    # get all categories
    category_container = page.locator("div.css-jamj16")
    category_locators = category_container.locator("div.css-z6s5c0 span")
    categories = await category_locators.all()
    # cleaned_categories = [category.strip() for category in categories]
    logger.debug(f"Cleaned Categories: {len(categories)} ")
    # print(cleaned_categories)
    return categories


async def expand_form(category_dd_label_locator, page):
    # click View All button
    view_all_btn_locator = (
        page.locator(".css-10xw46m button").filter(has_text="View All").first
    )
    btn_count = await view_all_btn_locator.count()
    logger.debug(f"View All button count: {btn_count}")
    if btn_count > 0:
        logger.debug("\tView All button found")
        await category_dd_label_locator.click(force=True)
        await page.wait_for_timeout(1000)
        await view_all_btn_locator.click(force=True)
        await view_all_btn_locator.evaluate("el => el.click()")
        await page.wait_for_timeout(1000)


# ------------------------------------------------------------------- #
async def crawl_page(browser: Browser, url: str, limiter: RateLimiter) -> List[Listing]:
    async with limiter:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_load_state("networkidle")

            await login_to_website(page)
            await goto_form(page)

            # get categories
            category_dd_label_selector = "div.css-79elbk span"
            category_dropdown_selector = "div.css-tf8u31 div.css-1dr1o9l button"
            category_dd_label_locator = page.locator(category_dd_label_selector).first
            categories = await get_all_category_locatora(
                category_dropdown_selector, page
            )

            await expand_form(category_dd_label_locator, page)

            count = 0
            for category in categories:
                await page.locator(category_dropdown_selector).first.evaluate(
                    "el => el.click()"
                )
                await page.wait_for_timeout(2000)
                await page.wait_for_selector(".MuiPopover-root")
                if not await category.is_visible():
                    raise Exception("Category is not visible")
                category_text = await category.text_content()
                logger.info(f"Clicking category: {category_text}")
                await category.click(force=True)
                await page.wait_for_timeout(1000)
                await category_dd_label_locator.click(force=True)
                await page.wait_for_timeout(1000)
                # await page.screenshot(
                #     path=f"output/after_category_click_{category}.png", full_page=True
                # )

                # get item spec fields
                item_spec_locator = (
                    # page.locator("div.css-rdzyjul")
                    page.locator("div")
                    .get_by_text("Item Specifics")
                    .locator("..")
                    .locator("..")
                    .locator("..")
                    .locator("..")
                    .first
                )
                if await item_spec_locator.count() == 0:
                    raise Exception(
                        f"Cannot found item spec locator for {category_text}"
                    )
                logger.info(f"Found item spec locator for {category_text}")
                field_locators = (
                    await page.locator("div")
                    .get_by_text("Item Specifics")
                    .locator("..")
                    .locator("..")
                    .locator("..")
                    .locator("..")
                    .first.locator("div.css-1ddqjgm")
                    .all()
                )
                for field in field_locators:
                    label_locator = field.locator("span")
                    label_text = await label_locator.text_content()
                    field_input_locator = field.locator("input[type='text']")
                    await field_input_locator.focus()
                    await page.wait_for_timeout(1000)
                    input_options = page.locator("div.MuiPopover-root")

                    if await input_options.count() == 0:
                        logger.debug("\tNo options")
                        options = []
                    else:
                        options_locators = input_options.locator("span")
                        options = await options_locators.all_text_contents()
                    logger.debug(
                        f'\tLabel: "{label_text}", Options Count: {len(options)}'
                    )

                await category_dd_label_locator.click(force=True)
                await page.wait_for_timeout(300)
                count += 1
                logger.info(
                    f"progress: {category_text} - {count}/{len(categories)}]]\n***************************\n"
                )

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
    # Create temp dir if needed (safe in async)
    user_data_dir = "/tmp/playwright-chrome-profile"
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        # Let PWDEBUG control headless/headful
        browser = await pw.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
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

        # ---- simple pagination example (adapt to real site) ----
        # tasks = [bounded_crawl(START_URL)]
        # for fut in tqdm_asyncio.as_completed(tasks, desc="Pages"):
        #     results.extend(await fut)
        # --- DEBUGGING: Run the task directly to see Inspector URL ---
        logger.info("Starting crawl task directly for debugging...")
        crawl_results = await bounded_crawl(START_URL)
        results.extend(crawl_results)
        logger.info("Crawl task finished.")
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
