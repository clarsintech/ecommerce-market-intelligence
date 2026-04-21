from database.queries import (get_session, save_scraped_product, get_session, start_scraping_log, finish_scraping_log, get_all_products, get_price_history, insert_product, insert_price_snapshot, insert_keyword, insert_product_keyword, get_all_asins, insert_scraped_product)
from scraper.amazon_scraper import  fetch_search_results_async, fetch_html_async, fetch_html
from scraper.parser import process_html, process_search_results
import time

import asyncio
import threading
import concurrent.futures

def run_async_in_thread(coro):
    result = None
    exception = None
    
    def thread_target():
        nonlocal result, exception
        # ✅ Tambahkan ini — set ProactorEventLoop untuk Windows
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            exception = e
        finally:
            loop.close()
    
    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    
    if exception:
        raise exception
    return result

async def process_search_tasks_async(keyword, max_results):
    keyword_url = keyword.replace(' ', '+')
    url = f'https://www.amazon.com/s?k={keyword_url}'
    
    try:
        products_session = get_session()
        
        # Jalankan playwright di thread terpisah
        html = run_async_in_thread(fetch_search_results_async(url))
        
        if not html:
            return []
        
        res = process_search_results(html, max_results)
        return res
        
    finally:
        products_session.close()
        
# Versi sync — dipanggil dari scheduler.py atau terminal
def process_search_tasks(keyword, max_results):
    return asyncio.run(process_search_tasks_async(keyword, max_results))

async def save_watchlist_products(asins, keyword):
    counter = 0 
    try:
        print(asins)
        print('In Save_watchlist_products')
        for asin in asins:
            product_session = get_session()
            try:
                product = await get_product_details(product_session, asin)
                if product:
                    keyword_node = insert_keyword(session=product_session, keyword=keyword)
                    product_keyword = insert_product_keyword(session=product_session, keyword_id=keyword_node.id, product_id=product.id)
                    
                    counter+=1
                    print('Sucessfully save_watchlist_product')    
        
            except Exception as e:
                print(f"Error saving {asin}: {e}")
            finally:
                product_session.close() # 🟢 Pastikan ditutup di sini
    except Exception as e:
        print(f'Error in save_watchlist_products: {e}')
        return
    return counter
    
async def get_product_details(session, ASIN):
    try:
        url = f'https://www.amazon.com/dp/{ASIN}'
        
        html = await fetch_html_async(url)

        if not html or html in ['NO_PRODUCT', 'WRONG_KEYWORD']:
            return None
        res = process_html(html)

        if res:
            product = insert_scraped_product(
                session=session,
                asin=res['ASIN'],
                title=res['title'],
                price=res['price'],
                original_price=res['original_price'],
                brand=res['brand'],
                category=res['category'],
                image_url=res['image_url'],
                is_prime=res['is_prime'],
                is_in_stock=res['is_in_stock'],
                rating=res['rating'],
                review_count=res['review_count'],
            )
            return product
    except Exception as e:
        print(f"Detail error: {e}")
        return None

async def process_task():

    # 🟢 1. START LOG (sekali saja)
    
    try:
        session = get_session()
        log = start_scraping_log(session)
        
        if not log:
            print("❌ Failed to start scraping log")
            return

        print(f"🚀 Scraping started at {log.started_at}")
        print(f'Log ID => {log.id}')
        
        session.close()

        asins = get_all_asins(session)
        products_failed = 0
        products_scraped = 0
        
        # 🟡 2. LOOP SEMUA PRODUK
        for a in asins:

            print(a)
            product_session = get_session()
            try:
                url = f'https://www.amazon.com/dp/{a.asin}'
                
                html = run_async_in_thread(fetch_html_async(url))

                if not html:
                    products_failed += 1
                    continue

                res = process_html(html)

                if res:
                    price_snapshot = save_scraped_product(
                        session=product_session,
                        asin=res['ASIN'],
                        title=res['title'],
                        price=res['price'],
                        original_price=res['original_price'],
                        brand=res['brand'],
                        category=res['category'],
                        image_url=res['image_url'],
                        is_prime=res['is_prime'],
                        is_in_stock=res['is_in_stock'],
                        rating=res['rating'],
                        review_count=res['review_count'],
                    )
                    if not price_snapshot:
                        products_failed+=1
                    else:                        
                        products_scraped+=1
                else:
                    products_failed += 1

            finally:
                product_session.close()

        session = get_session()
        # 🔴 3. FINISH LOG (sekali saja)
        log = finish_scraping_log(
            session=session,
            log_id=log.id,
            products_scraped=products_scraped,
            products_failed=products_failed
        )

        print(f"✅ Scraping finished at {log.finished_at}")
        session.close()
    finally:
        session.close()
    
    return products_scraped


def get_all_data():
    session = get_session()
    products = get_all_products(session)
    
    for p in products:
        print(f'Product Name: {p.title}')
        price_histories = get_price_history(session, p.id)
        for ph in price_histories:
            print(f'Price: {ph.price}')
            print(f'Discount: {round(ph.discount_pct, 2)}%')
            print(f'Rating: {ph.rating}')
            print(f'Review Count: {ph.review_count}')
    return

async def fetch_with_retry_async(url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        html = await fetch_search_results_async(url)
        
        if html and "Something went wrong" not in html and "sorry" not in html.lower():
            return html  # berhasil
        
        print(f"Attempt {attempt} gagal, tunggu {attempt * 30} detik...")
        await asyncio.sleep(attempt * 30)  # tunggu 30s, 60s, 90s
    
    return None  # semua retry gagal

def fetch_with_retry(url, retries=3):
    for i in range(retries):
        html = fetch_html(url)

        if html == "NO_PRODUCT":
            return None  # 🔥 langsung stop retry

        if html:
            return html

        print(f"Retry {i+1} for {url}")
        time.sleep(2)

    return None

# process_task()
# get_all_data()
