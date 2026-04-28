from sqlalchemy import create_engine, select, func, asc, desc
# create_engine create connection to db
from database.models import Product, PriceSnapshot, ScrapingLog, Keyword, ProductKeyword
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL

from datetime import datetime, timedelta

# 🔥 bikin engine sekali
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=180
)

# 🔥 session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False  # 🔥 matikan autoflush global
)
# 🔥 helper ambil session 
def get_session():
    return SessionLocal()

def get_session_with_retry(retries=3):
    for i in range(retries):
        try:
            return get_session()
        except OperationalError:
            print(f'DB connect retry {i+1}')
            datetime.sleep(2)
    raise Exception('DB connection failed')

#--------------------- Keyword Queries

def insert_keyword(session, keyword):
    try:
        existing = session.scalar(select(Keyword).where(Keyword.name == keyword))  
        
        if existing:
            return existing
        
        # If the product is not avail, then insert product
        keyword = Keyword(name=keyword)
        session.add(keyword)
        session.commit()
        print(f"✅ Keyword '{keyword}' sucessfully inserted!")
        return keyword
    
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Error insert_keyword: {e}')
        return None

def insert_product_keyword(session, keyword_id, product_id):
    try:
        # If the product is not avail, then insert product
        product_keyword = ProductKeyword(
            keyword_id=keyword_id, 
            product_id=product_id
        )
        session.add(product_keyword)
        session.commit()
        print(f"✅ Product Keyword sucessfully inserted!")
        return product_keyword
    
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Error insert_product_keyword: {e}')
        return None

#--------------------- Product Queries

def insert_product(session, asin, title, brand, category, image_url):
    print('Masuk')
    
    try:
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
            created_at = datetime.now()
        )
        session.add(product)
        session.commit()
        print(f"✅ Product '{title}' sucessfully inserted!")
        return product
    
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Error insert_product: {e}')
        return None

def get_latest_products(session):
    latest_snapshot = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            PriceSnapshot.discount_pct,
            PriceSnapshot.is_in_stock,
            PriceSnapshot.review_count,
            PriceSnapshot.rating,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc(),
            )
            .label("prev_price"),
            func.row_number()
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.desc(),
            )
            .label("rn"),
        )
    ).subquery()

    keyword_subq = (
        select(
            ProductKeyword.product_id.label("product_id"),
            func.min(Keyword.name).label("keyword_name"),
        )
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        .group_by(ProductKeyword.product_id)
        .subquery()
    )

    change = (
        latest_snapshot.c.price
        - func.coalesce(latest_snapshot.c.prev_price, latest_snapshot.c.price)
    ).label("change")

    stmt = (
        select(
            Product.id.label("product_id"),
            Product.asin,
            Product.title,
            Product.brand,
            Product.image_url,
            latest_snapshot.c.price,
            latest_snapshot.c.prev_price,
            change,
            latest_snapshot.c.discount_pct,
            latest_snapshot.c.scraped_at,
            latest_snapshot.c.is_in_stock,
            latest_snapshot.c.review_count,
            latest_snapshot.c.rating,
            keyword_subq.c.keyword_name,
        )
        .join(latest_snapshot, Product.id == latest_snapshot.c.product_id)
        .outerjoin(keyword_subq, keyword_subq.c.product_id == Product.id)
        .where(latest_snapshot.c.rn == 1)
        .order_by(desc(latest_snapshot.c.scraped_at))
    )

    return session.execute(stmt).mappings().all()

def get_all_asins(session):
    # tampilkan semua produk asins
    result = session.execute(select(Product.asin, Product.brand)).all()
    return result
    

#------------------- Pricing Queries
def insert_price_snapshot(session, product_id, price, original_price, is_prime, is_in_stock, rating, review_count):

    try:
        price_snapshot = PriceSnapshot(
            product_id = product_id,
            price = price,
            original_price = original_price,
            discount_pct = round((original_price - price)/original_price * 100,2) if original_price > 0 else 0,
            is_prime = is_prime,
            is_in_stock = is_in_stock,
            rating = rating,
            review_count = review_count
        )

        session.add(price_snapshot)
        session.commit()
        print(f"Price Snapshot added!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Error insert_price_snapshot: {e}')
        return None
                   
    return price_snapshot

def get_price_history(session, product_asin):
    # bikin chart harga naik turun
    try:
        stmt = (
            select(
                PriceSnapshot.product_id,
                PriceSnapshot.price,
                PriceSnapshot.original_price,
                PriceSnapshot.discount_pct,
                PriceSnapshot.is_prime,
                PriceSnapshot.is_in_stock,
                PriceSnapshot.rating,
                PriceSnapshot.review_count,
                PriceSnapshot.scraped_at
            )
            .join(Product, Product.id == PriceSnapshot.product_id)
            .where(Product.asin == product_asin)
            .order_by(PriceSnapshot.scraped_at.asc())
        )
        
        # scalars() digunakan untuk mengambil objek PriceSnapshot utuh
        price_histories = session.execute(stmt).mappings().all()
        
        return price_histories
    except Exception as e:
        print(f"Error pada query: {e}")
        return []

def get_biggest_product_discount(session):
    ranked = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            PriceSnapshot.is_in_stock,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc()
            )
            .label("prev_price")
        )
    ).subquery()

    price_diff = (ranked.c.price - ranked.c.prev_price).label("discount")
    # buat logic biar scrapednya yg hari ini juga biar gk aneh datanya
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)
    
    stmt = (
        select(ranked, Product.title, Product.asin, Product.brand, price_diff)
        .join(Product, Product.id == ranked.c.product_id)
        .where(ranked.c.prev_price.isnot(None))
        .where(ranked.c.prev_price > 0)
        .where(ranked.c.price != ranked.c.prev_price)
        .where(ranked.c.scraped_at >= today_start)
        .where(ranked.c.scraped_at < tomorrow)
        .order_by(asc('discount'))
        .limit(1)
    )

    result = session.execute(stmt).mappings().first()
    
    return result

def get_price_drop_products(session):
    # Subquery: ambil 2 snapshot terakhir per produk
    ranked = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            PriceSnapshot.is_in_stock,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc(),
            )
            .label("prev_price"),
            func.row_number()
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.desc(),
            )
            .label("rn"),
        )
    ).subquery()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)

    stmt = (
        select(
            ranked, 
            Product.title, 
            Product.asin, 
            Product.brand,
            Keyword.name.label("keyword_name")
        )
        
        .join(Product, Product.id == ranked.c.product_id)
        .join(ProductKeyword, Product.id == ProductKeyword.product_id)
        .join(Keyword, ProductKeyword.keyword_id == Keyword.id)
        
        .where(ranked.c.rn == 1)
        .where(ranked.c.is_in_stock.is_(True))
        .where(ranked.c.prev_price.isnot(None))
        .where(ranked.c.prev_price > 0)
        .where(ranked.c.price != ranked.c.prev_price)
        .where(ranked.c.scraped_at >= today_start)
        .where(ranked.c.scraped_at < tomorrow)
        
        .order_by(ranked.c.scraped_at.desc())
    )

    return session.execute(stmt).mappings().all()

#------------------- Scraping Queries
def start_scraping_log(session):
    try:
        log = ScrapingLog(
            status = "running",
            products_scraped=0,
            products_failed=0,
            started_at=datetime.now()
        )
        session.add(log)
        session.commit()
        return log
    except OperationalError as e:
        session.rollback()
        print(f'start_scraping_log error: {e}')
        return None
        
def finish_scraping_log(session, log_id, products_scraped, products_failed, error_message=None):
    log = session.get(ScrapingLog, log_id) 
    if log:
        try:
            log.status = "success" if products_failed == 0 else "partial" if products_scraped > 0 else "failed"
            log.products_scraped = products_scraped
            log.products_failed = products_failed
            log.error_message = error_message
            log.finished_at = datetime.now() 
            session.commit()
            print(f"✅ Log updated! {products_scraped} scraped, {products_failed} failed.")
            return log
            
        except Exception as e:
            session.rollback()
            print(f'Error finish_scraping_log: {e}')
            return None
    return None

def insert_scraped_product(session, asin, title, price, original_price, brand, category, image_url, is_prime, is_in_stock, rating, review_count):
    try:
        with session.no_autoflush:
            product = insert_product(session, asin, title, brand, category, image_url)
            
            price_snapshot = insert_price_snapshot(session, product.id, price, original_price, is_prime, is_in_stock, rating, review_count)
                
            try:
                session.commit()
            except:
                session.rollback()
        
    except SQLAlchemyError as e:
        session.rollback()  # penting kalau ada transaksi
        print(f"Database error: {e}")

    # scraper jalan, product 1 -> save_scraped_product() -> hasil -> scraped += 1

    return product

def save_scraped_product(session, asin, title, price, original_price, brand, category, image_url, is_prime, is_in_stock, rating, review_count):
    # kalau baru, insert. kalau lama, skip insert_product()
    # karna di insert_product udah ada logicnya, berarti langsung pake aja functionnya
    try:
        with session.no_autoflush:
            product = insert_product(session, asin, title, brand, category, image_url)
            if not product:
                return None
            
            price_snapshot = insert_price_snapshot(session, product.id, price, original_price, is_prime, is_in_stock, rating, review_count)

            if not price_snapshot:
                return None
                
            try:
                session.commit()
            except:
                session.rollback()
        
    except SQLAlchemyError as e:
        session.rollback()  # penting kalau ada transaksi
        print(f"Database error: {e}\n ASIN=>{asin}")
        return None

    # scraper jalan, product 1 -> save_scraped_product() -> hasil -> scraped += 1

    return price_snapshot

def get_last_scraped_at(session):
    stmt = (
        select(
            ScrapingLog.status,
            ScrapingLog.finished_at,
            ScrapingLog.products_scraped,
            ScrapingLog.products_failed,
        ).order_by(ScrapingLog.finished_at.desc()).limit(1)
        
    )
    result = session.execute(stmt).mappings().first()
    return result

#-------------------- Keyword Grouping Queries
def get_all_keywords(session):
    stmt = select(Keyword)
    keywords = session.scalars(stmt).all()
    
    return keywords