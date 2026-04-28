import asyncio
import random

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

SEARCH_RESULT_SELECTOR = 'div[role="listitem"][data-asin]:not([data-asin=""])'
PRODUCT_TITLE_SELECTOR = "#productTitle"

def is_search_url(url):
    return "s?k=" in url

def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def human_delay(min_seconds = 1.0, max_seconds = 3.0):
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))
    
async def human_mouse_move(page):
    await page.mouse.move(
        random.randint(100, 500),
        random.randint(100, 400)
    )
    
async def block_heavy_resources(page):
    async def handle_route(route):
        resource_type = route.request.resource_type
        
        if resource_type in ['image', 'font', 'media']:
            await route.abort()
        else:
            await route.continue_()
    
    await page.route('**/*', handle_route)
    
async def create_browser_context(playwright):
    browser = await playwright.chromium.launch(
        headless = True,
        args = BROWSER_ARGS
    )
    
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=get_random_user_agent(),
        ignore_https_errors=True,
        locale="en-US",
        timezone_id="America/New_York",
    )

    await context.add_cookies([{
        "name": "i18n-prefs",
        "value": "USD",
        "domain": ".amazon.com",
        "path": "/",
    }])

    return browser, context

async def prepare_page(context):
    page = await context.new_page()

    await block_heavy_resources(page)

    stealth = Stealth()
    await stealth.apply_stealth_async(page)

    return page


async def is_bot_check_page(page):
    html = await page.content()
    lower_html = html.lower()

    bot_signals = [
        "enter the characters you see below",
        "not a robot",
        "captcha",
        "sorry, we just need to make sure",
    ]

    return any(signal in lower_html for signal in bot_signals)


async def wait_for_expected_content(page, url):
    if is_search_url(url):
        try:
            await page.wait_for_selector(SEARCH_RESULT_SELECTOR, timeout=10000)
            return None
        except PlaywrightTimeoutError:
            return "WRONG_KEYWORD"

    try:
        await page.wait_for_selector(PRODUCT_TITLE_SELECTOR, timeout=8000)
        return None
    except PlaywrightTimeoutError:
        return "NO_PRODUCT"

async def fetch_page_html(url, retries = 3):
    for attempt in range(1, retries + 1):
        browser = None

        try:
            async with async_playwright() as playwright:
                browser, context = await create_browser_context(playwright)
                page = await prepare_page(context)

                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                await human_delay(2, 5)
                await human_mouse_move(page)
                await human_delay(1, 2)

                if await is_bot_check_page(page):
                    print(f"⚠️ Bot check detected on attempt {attempt}")
                    await page.screenshot(
                        path=f"debug_bot_check_attempt_{attempt}.png",
                        full_page=True,
                    )
                    return None

                page_status = await wait_for_expected_content(page, url)

                if page_status:
                    print(f"⚠️ {page_status} on attempt {attempt}")

                    if attempt == retries:
                        return page_status

                    await human_delay(2, 4)
                    continue

                return await page.content()

        except PlaywrightTimeoutError:
            print(f"⏳ Page load timeout on attempt {attempt}")

        except Exception as error:
            print(f"❌ Unexpected error on attempt {attempt}: {error}")

        finally:
            if browser:
                await browser.close()

        await human_delay(2, 4)

    return None

async def fetch_search_results_async(url):
    return await fetch_page_html(url, retries = 3)
        
async def fetch_html_async(url, retries=3):
    return await fetch_page_html(url, retries)
        
def fetch_html(url):
    return asyncio.run(fetch_html_async(url))

def fetch_search_results(url):
    return asyncio.run(fetch_search_results_async(url))