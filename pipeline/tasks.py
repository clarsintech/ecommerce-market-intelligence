import asyncio
import sys
import time

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from database.queries import (
    get_session, 
    save_scraped_product, 
    start_scraping_log, 
    finish_scraping_log, 
    get_latest_products,
    get_price_history, 
    insert_keyword, 
    insert_product_keyword, 
    get_all_asins, 
    insert_scraped_product)
from scraper.amazon_scraper import  fetch_search_results_async, fetch_html_async, fetch_html
from scraper.parser import process_html, process_search_results

# ─────────────────────────────────────────────
# Search Products
# ─────────────────────────────────────────────

async def process_search_tasks_async(keyword, max_results):
    keyword_url = keyword.strip().replace(' ', '+')
    url = f'https://www.amazon.com/s?k={keyword_url}'
    
    html = await fetch_search_results_async(url)

    if not html:
        return []
    
    return process_search_results(html, max_results)
        
# Versi sync — dipanggil dari scheduler.py atau terminal
def process_search_tasks(keyword, max_results):
    return asyncio.run(process_search_tasks_async(keyword, max_results))

# ─────────────────────────────────────────────
# Save Watchlist
# ─────────────────────────────────────────────

async def save_watchlist_products(asins, keyword):
    counter = 0 
    print(asins)
    print('In Save_watchlist_products')
    for asin in asins:
        session = get_session()
        try:
            product = await get_product_details(session, asin)
            
            if not product:
                continue
            
            keyword_node = insert_keyword(session=session, keyword=keyword)
            
            insert_product_keyword(session=session, keyword_id=keyword_node.id, product_id=product.id)
            
            counter+=1
            print('Sucessfully save_watchlist_product')    
    
        except Exception as e:
            print(f"Error saving {asin}: {e}")
            
        finally:
            session.close() # 🟢 Pastikan ditutup di sini
    
    return counter
    
async def get_product_details(session, ASIN):
    url = f'https://www.amazon.com/dp/{ASIN}'
    
    try:
        
        html = await fetch_html_async(url)

        if not html or html in ['NO_PRODUCT', 'WRONG_KEYWORD']:
            return None
        
        result = process_html(html)

        if not result:
            return None
        
        return insert_scraped_product(
            session=session,
            asin=result['ASIN'],
            title=result['title'],
            price=result['price'],
            original_price=result['original_price'],
            brand=result['brand'],
            category=result['category'],
            image_url=result['image_url'],
            is_prime=result['is_prime'],
            is_in_stock=result['is_in_stock'],
            rating=result['rating'],
            review_count=result['review_count'],
        )
        
    except Exception as e:
        print(f"Detail error for {ASIN}: {e}")
        return None
    
# ─────────────────────────────────────────────
# Update Existing Watchlist Prices
# ─────────────────────────────────────────────

async def process_task():

    # 🟢 1. START LOG (sekali saja)
    session = get_session()
    log = None
    
    try:
        log = start_scraping_log(session)
        
        if not log:
            print("❌ Failed to start scraping log")
            return

        print(f"🚀 Scraping started at {log.started_at}")
        print(f'Log ID => {log.id}')
        
        asins = get_all_asins(session)
        
    finally:
        session.close()
        
    products_scraped = 0
    products_failed = 0

    # 🟡 2. LOOP SEMUA PRODUK
    for product in asins:
        success = await scrape_and_save_product(product.asin)

        if success:
            products_scraped += 1
        else:
            products_failed += 1

    session = get_session()

    try:
        finished_log = finish_scraping_log(
            session=session,
            log_id=log.id,
            products_scraped=products_scraped,
            products_failed=products_failed,
        )

        print(f"✅ Scraping finished at {finished_log.finished_at}")

    finally:
        session.close()

    return products_scraped

async def scrape_and_save_product(asin):
    session = get_session()
    url = f"https://www.amazon.com/dp/{asin}"

    try:
        html = await fetch_html_async(url)

        if not html or html in ["NO_PRODUCT", "WRONG_KEYWORD"]:
            return False

        result = process_html(html)

        if not result:
            return False

        price_snapshot = save_scraped_product(
            session=session,
            asin=result["ASIN"],
            title=result["title"],
            price=result["price"],
            original_price=result["original_price"],
            brand=result["brand"],
            category=result["category"],
            image_url=result["image_url"],
            is_prime=result["is_prime"],
            is_in_stock=result["is_in_stock"],
            rating=result["rating"],
            review_count=result["review_count"],
        )

        return price_snapshot is not None

    except Exception as error:
        print(f"Error scraping {asin}: {error}")
        return False

    finally:
        session.close()

def get_all_data():
    session = get_session()
    products = get_latest_products(session)
    
    for p in products:
        print(f'Product Name: {p.title}')
        price_histories = get_price_history(session, p.id)
        for ph in price_histories:
            print(f'Price: {ph.price}')
            print(f'Discount: {round(ph.discount_pct, 2)}%')
            print(f'Rating: {ph.rating}')
            print(f'Review Count: {ph.review_count}')
    return

# ─────────────────────────────────────────────
# Retry Helpers
# ─────────────────────────────────────────────

async def fetch_with_retry_async(url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        html = await fetch_search_results_async(url)
        
        if html and "Something went wrong" not in html and "sorry" not in html.lower():
            return html  # berhasil
        
        print(f"Attempt {attempt} gagal, tunggu {attempt * 30} detik...")
        await asyncio.sleep(attempt * 30)  # tunggu 30s, 60s, 90s
    
    return None  # semua retry gagal

def fetch_with_retry(url, retries=3):
    for attempt in range(1, retries + 1):
        html = fetch_html(url)

        if html == "NO_PRODUCT":
            return None  # 🔥 langsung stop retry

        if html:
            return html

        print(f"Retry {attempt} for {url}")
        time.sleep(2)

    return None

asyncio.run(process_task())