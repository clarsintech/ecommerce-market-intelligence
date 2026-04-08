from sqlalchemy import create_engine, select, func
# create_engine create connection to db
from sqlalchemy.orm import Session, aliased # our work session with db
from database.models import Base, Product, PriceSnapshot, ScrapingLog, init_db
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime, timedelta

def get_engine(db_path="market_intel.db"):
    return create_engine(f"sqlite:///{db_path}")

# def get_engine(db_path=None):
#     from config.settings import DATABASE_URL
#     url = f"sqlite:///{db_path}" if db_path else DATABASE_URL
#     return create_engine(url)

def get_session(engine):
    return Session(engine)

#--------------------- Product Queries

def insert_product(session, asin, title, brand, category, image_url):
    print('Masuk')
    # Checks if the product is available in db using ASIN
    existing = session.scalar(select(Product).where(Product.asin == asin)) #scalar untuk keluarin result pertama
    
    
    if existing:
        print(f"The product {asin} is already in db, skip.")
        return existing
    
    # If the product is not avail, then insert product
    product = Product(
        asin=asin,
        title=title,
        brand=brand,
        category=category,
        image_url=image_url,
    )
    session.add(product)
    session.commit()
    print(f"✅ Product '{title}' sucessfully inserted!")
    return product

def get_all_products(session):
    # tampilkan semua produk di tabel
    all_products = session.scalars(select(Product)).all()

    return all_products

#------------------- Pricing Queries

def insert_price_snapshot(session, product_id, price, original_price, is_prime, is_in_stock, rating, review_count):

    price_snapshot = PriceSnapshot(
        product_id = product_id,
        price = price,
        original_price = original_price,
        discount_pct = (original_price - price)/original_price * 100 if original_price > 0 else 0,
        is_prime = is_prime,
        is_in_stock = is_in_stock,
        rating = rating,
        review_count = review_count
    )

    session.add(price_snapshot)
    session.commit()
    print(f"Price Snapshot added!")
    
    return price_snapshot

def get_price_history(session, product_id):
    # bikin chart harga naik turun
    price_histories = session.scalars(select(PriceSnapshot).where(PriceSnapshot.product_id == product_id).order_by(PriceSnapshot.scraped_at.asc())).all()

    return price_histories

def get_latest_price_all(session):
    # harga terbaru semua produk sekaligus
    subq = (
        select(
            PriceSnapshot.product_id,
            func.max(
                PriceSnapshot.scraped_at
            ).label("latest_date")
        )
        .group_by(PriceSnapshot.product_id)
        .subquery()
    )

    stmt = (
        select(Product, PriceSnapshot)
        .join(PriceSnapshot, Product.id == subq.c.product_id)
        .join(subq, (PriceSnapshot.product_id == subq.c.product_id) & (PriceSnapshot.scraped_at == subq.c.latest_date))
    )

    latest_prices = session.execute(stmt).all()

    return latest_prices

def get_products_rating_and_review(session, product_id):
    
    result = session.execute(select(PriceSnapshot.rating, PriceSnapshot.review_count, PriceSnapshot.scraped_at).where(PriceSnapshot.product_id == product_id).order_by(PriceSnapshot.scraped_at.asc())).all()
    
    return result

def get_products_with_price_drop(session):
    # deteksi produk yang harganya turun hari ini
    
    # lag() untuk dapat data sebelumnya, jadi pakai asc 

    stmt = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc()
            )
            .label("prev_price")
        )
    )

    subq = stmt.subquery()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)

    final = (
        select(subq)
        .where(subq.c.prev_price.isnot(None))
        .where(subq.c.scraped_at >= today_start)
        .where(subq.c.scraped_at < tomorrow)
    )

    result = session.execute(final).all()

    return result
    
def get_price_alerts(session, threshold_pct=5.0):
    """
    Ambil produk yang harganya turun lebih dari threshold_pct
    dibanding snapshot sebelumnya.
    """
    # Subquery: ambil 2 snapshot terakhir per produk
    ranked = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc()
            )
            .label("prev_price")
        )
    ).subquery()

    # Filter yang harganya turun melebihi threshold
    stmt = (
        select(ranked, Product.title, Product.asin, Product.brand)
        .join(Product, Product.id == ranked.c.product_id)
        .where(ranked.c.prev_price.isnot(None))
        .where(
            ((ranked.c.prev_price - ranked.c.price) / ranked.c.prev_price * 100)
            >= threshold_pct
        )
        .order_by(ranked.c.scraped_at.desc())
    )

    return session.execute(stmt).all()

#------------------- Scraping Queries

def start_scraping_log(session):
    log = ScrapingLog(
        status = "running",
        products_scraped=0,
        products_failed=0,
        started_at=datetime.utcnow()
    )
    session.add(log)
    session.commit()
    return log

def finish_scraping_log(session, log, products_scraped, products_failed, error_message=None):
    log.status = "success" if products_failed == 0 else "partial" if products_scraped > 0 else "failed"
    log.products_scraped = products_scraped
    log.products_failed = products_failed
    log.error_message = error_message
    log.finished_at = datetime.utcnow() 
    
    session.commit()
    print(f"✅ Log updated! {products_scraped} scraped, {products_failed} failed.")
    
    return log

def save_scraped_product(session, asin, title, price, original_price, log, brand, category, image_url, is_prime, is_in_stock, rating, review_count):
    # kalau baru, insert. kalau lama, skip insert_product()
    # karna di insert_product udah ada logicnya, berarti langsung pake aja functionnya
    try:
        # print(asin)
        # print(title)
        # print(brand)
        product = insert_product(session, asin, title, brand, category, image_url)
        
        # selalu insert harga baru insert_price_snapshot()
        price_snapshot = insert_price_snapshot(session, product.id, price, original_price, is_prime, is_in_stock, rating, review_count)
    
        log.products_scraped+=1
        
    except SQLAlchemyError as e:
        session.rollback()  # penting kalau ada transaksi
        log.products_failed+=1
        print(f"Database error: {e}")

    # scraper jalan, product 1 -> save_scraped_product() -> hasil -> scraped += 1

    return log

