# import sys
# import os

# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
# if ROOT_DIR not in sys.path:
#     sys.path.append(ROOT_DIR)
from scraper.amazon_scraper import fetch_html
from scraper.parser import process_html
from database.queries import save_scraped_product, get_session, get_engine, start_scraping_log, finish_scraping_log, get_all_products, get_price_history

def process_task():
    
    asins = [
    # "B00FLYWNYQ",
    # "B07FZ8S74R",
    # "B08N5WRWNW",
    "B00Y9X0L2G",
    "B0BDHWDR12",
    "B07FDJMC9Q",
    "B01MSSDEPK",
    "B07C5G3F1H",
    "B07YF8KZ9Z",
    "0307465357"
    ]
    
    engine = get_engine()
    session = get_session(engine=engine)
    
    # log = start_scraping_log(session=session)
    # print(f'Log=>{log.status}')
    
    for a in asins:
        url = f'https://www.amazon.com/dp/{a}'
        html = fetch_html(url)
        res = process_html(html)    
        # if res:
            # log = save_scraped_product(session=session, asin=res['ASIN'], title=res['title'], price=res['price'], original_price=res['original_price'], log=log, brand=res['brand'], category=res['category'], image_url=res['image_url'], is_prime=res['is_prime'], is_in_stock=res['is_in_stock'], rating=res['rating'], review_count=res['review_count'])
    
        # else:
            # log.products_failed+=1    
    
    # log = finish_scraping_log(session=session, log=log, products_scraped=log.products_scraped, products_failed=log.products_failed)
    
    return


def get_all_data():
    engine = get_engine()
    session = get_session(engine=engine)
    products = get_all_products(session)
    
    for p in products:
        print(f'Product Name: {p.title}')
        price_histories = get_price_history(session, p.id)
        for ph in price_histories:
            print(f'Price: {ph.price}')
            print(f'Discount: {ph.discount_pct}%')
            print(f'Rating: {ph.rating}')
            print(f'Review Count: {ph.review_count}')
    return


# process_task()
# get_all_data()