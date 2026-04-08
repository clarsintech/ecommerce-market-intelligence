from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random

def fetch_html(url):

    with sync_playwright() as p:
        # Launch browser - headless=False supaya kamu bisa lihat browsernya buka
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            viewport={"width":1280,"height":800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        page.goto(url, wait_until="domcontentloaded")
        
        # Simulate manusia — scroll pelan-pelan
        time.sleep(random.uniform(2, 4))
        page.mouse.move(random.randint(100, 500), random.randint(100, 400))
        time.sleep(random.uniform(1, 2))

        try:
            print('Test')
            page.wait_for_selector("#productTitle", timeout=5000)
            # page.wait_for_selector("#productTitle")

            html = page.content()
            browser.close()
            return html
        
        except:
            browser.close()
            return 