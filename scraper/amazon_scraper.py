from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import asyncio
import random


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

async def fetch_search_results_async(url):

    async with async_playwright() as p:
        # Launch browser - headless=False supaya kamu bisa lihat browsernya buka
        browser = await p.chromium.launch(
            # headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )


        context = await browser.new_context(
            viewport={"width":1280,"height":800},
            user_agent=random.choice(USER_AGENTS),
            ignore_https_errors=True,
            # locale="en-US",
            # timezone_id="America/New_York"
        )
        
        await context.add_cookies([{
            "name": "i18n-prefs",
            "value": "USD",
            "domain": ".amazon.com",
            "path": "/"
        }])

        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(5, 10))
            await page.mouse.move(random.randint(100, 500), random.randint(100, 400))
            await asyncio.sleep(random.uniform(1, 2))
            if "s?k=" in url:
                try:
                    await page.wait_for_selector('div[role="listitem"][data-asin]:not([data-asin=""])', timeout=10000)
                except PlaywrightTimeoutError:
                    print('Products with that keyword not available!')
                    return 'WRONG_KEYWORD'

            html = await page.content()
            await browser.close()
            return html

        except PlaywrightTimeoutError:
            print("⏳ Page load timeout, retryable...")
            return None

        finally:
            await browser.close()
        
async def fetch_html_async(url, retries=3):
    for attempt in range(retries):
        async with async_playwright() as p:
            # Launch browser - headless=False supaya kamu bisa lihat browsernya buka
            browser = await p.chromium.launch(
                # headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            context = await browser.new_context(
                viewport={"width":1280,"height":800},
                user_agent=random.choice(USER_AGENTS),
                ignore_https_errors=True,
                # locale="en-US",
                # timezone_id="America/New_York"
            )
            
            await context.add_cookies([{
                "name": "i18n-prefs",
                "value": "USD",
                "domain": ".amazon.com",
                "path": "/"
            }])

            page = await context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                # Contoh mematikan gambar agar loading ngebut
                await page.route("**/*.{png,jpg,jpeg,svg}", lambda route: route.abort())
                await asyncio.sleep(random.uniform(1, 2))
                await page.mouse.move(random.randint(100, 500), random.randint(100, 400))
                await asyncio.sleep(random.uniform(1, 2))
                if "s?k=" in url:
                    try:
                        await page.wait_for_selector('div[role="listitem"][data-asin]:not([data-asin=""])', timeout=10000)
                    except PlaywrightTimeoutError:
                        print('Products with that keyword not available!')
                        return 'WRONG_KEYWORD'
                else:

                    try:
                        await page.wait_for_selector("#productTitle", timeout=5000)
                    except Exception as e:
                        print(f"❌ Product title not found (likely deleted), retry on attempt {attempt+1}: {e}")
                        await browser.close()
                        if attempt == retries - 1:
                            print("🚫 All retries failed.")
                            return None
                        await asyncio.sleep(2) # Kasih jeda sebelum coba lagi

                        
                        
                        return "NO_PRODUCT"  # 🔥 special flag

                html = await page.content()
                return html

            except Exception as e:
                print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    print("🚫 All retries failed.")
                    return None
                await asyncio.sleep(2) # Kasih jeda sebelum coba lagi

            finally:
                await browser.close()
    return None
        
def fetch_html(url):
    return asyncio.run(fetch_html_async(url))

def fetch_search_results(url):
    return asyncio.run(fetch_search_results_async(url))