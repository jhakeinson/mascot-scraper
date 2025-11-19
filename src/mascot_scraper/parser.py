from bs4 import BeautifulSoup
from playwright.async_api import Locator, Page
from typing import List
from loguru import logger
from .models import Field


async def login_to_website(username, password, page):
    # Interact with login form
    await page.get_by_placeholder("Enter email").fill(username)
    await page.get_by_placeholder("Enter password").fill(password)
    await page.get_by_role("button", name="Sign in").click()
    try:
        await page.wait_for_load_state("networkidle", timeout=10_000)
        await page.wait_for_timeout(10_000)
    except TimeoutError:
        print("Warning: Timeout while waiting after Sign In,")


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

    # get all categories
    category_container = page.locator("div.css-jamj16")
    category_locators = category_container.locator("div.css-z6s5c0 span")
    categories = await category_locators.all()
    logger.debug(f"Cleaned Categories: {len(categories)} ")
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


async def process_category_form(category_text, page):
    category_fields: List[Field] = []
    # get item spec fields
    item_spec_locator = (
        page.locator("div")
        .get_by_text("Item Specifics")
        .locator("..")
        .locator("..")
        .locator("..")
        .locator("..")
        .first
    )
    if await item_spec_locator.count() == 0:
        raise Exception(f"Cannot found item spec locator for {category_text}")
    logger.info(f"Found item spec locator for {category_text}")
    options: List[str] = []
    field_locators = await item_spec_locator.locator("div.css-1ddqjgm").all()
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

        cleaned_options = [option.strip() for option in options]
        category_fields.append(
            Field(
                category_name=category_text,
                form_label="Feature Specifics",
                field_label=label_text,
                # field type should be `select` or `text` depending if options is empty or not
                field_type="select" if len(options) > 0 else "text",
                # field values: vertical bar separated string of options,
                field_values=" | ".join(cleaned_options) if len(options) > 0 else "",
            )
        )
        logger.debug(f'\tLabel: "{label_text}", Options Count: {len(options)}')

    return category_fields


async def extract_form_data(page: Page) -> List[Field]:
    data = []
    # get categories
    category_dd_label_selector = "div.css-79elbk span"
    category_dropdown_selector = "div.css-tf8u31 div.css-1dr1o9l button"
    category_dd_label_locator = page.locator(category_dd_label_selector).first
    categories = await get_all_category_locatora(category_dropdown_selector, page)

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

        category_data = await process_category_form(category_text, page)
        if category_data is None:
            category_data = []
        # merge category_data with data
        data.extend(category_data)

        await category_dd_label_locator.click(force=True)
        await page.wait_for_timeout(300)
        count += 1
        logger.info(
            f"progress: {category_text} - {count}/{len(categories)}]]\n***************************\n"
        )

        # DEBUG: for debugging
        # if count > 2:
        #     break

    return data
