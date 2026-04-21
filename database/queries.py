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

# def get_engine(db_path="market_intel.db"):
#     return create_engine(f"sqlite:///{db_path}")

# def get_session(engine):
#     return Session(engine)

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

def get_all_products(session):
    # tampilkan semua produk di tabel
    all_products = []

    subq = (
        select(
            PriceSnapshot.product_id,
            PriceSnapshot.price,
            PriceSnapshot.scraped_at,
            PriceSnapshot.discount_pct,
            PriceSnapshot.is_in_stock,
            PriceSnapshot.review_count,
            func.lag(PriceSnapshot.price)
            .over(
                partition_by=PriceSnapshot.product_id,
                order_by=PriceSnapshot.scraped_at.asc()
            )
            .label('prev_price')
        )
    ).subquery()

    # coalesce(prev_price, price) artinya jika prev_price NULL, pakai harga sekarang (selisih jadi 0)
    change = (subq.c.price - func.coalesce(subq.c.prev_price, subq.c.price)).label("change")

    stmt = (
        select(
            Product.asin,
            Product.title,
            Product.brand,
            Product.image_url,
            subq.c.price,
            change,
            subq.c.discount_pct,
            subq.c.scraped_at,
            subq.c.review_count,
            Keyword.name
        )
        
        .join(subq, Product.id == subq.c.product_id)
        .join(ProductKeyword, Product.id == ProductKeyword.product_id)
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        .distinct(Product.asin)
        .order_by(Product.asin, desc(subq.c.scraped_at))
    )
    
    all_products = session.execute(stmt).mappings().all()

    return all_products

def get_all_products_with_grouping(session, keyword=None):
    stmt = ''
    if not keyword:
    
        stmt = (
        select(
            Product.asin.label("product_asin"),
            Product.title,
            Product.brand,
            PriceSnapshot.price,
            PriceSnapshot.discount_pct,
            Keyword.name.label("keyword_name")
        )
        # 1. Tentukan kolom mana yang harus unik (tidak boleh duplikat ASIN)
        .distinct(Product.asin) 
        
        .join(PriceSnapshot, Product.id == PriceSnapshot.product_id)
        .join(ProductKeyword, Product.id == ProductKeyword.product_id)
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        
        # 2. WAJIB: Order by kolom distinct dulu, baru kolom pengurutnya
        .order_by(
            Product.asin, 
            desc(PriceSnapshot.scraped_at)
        )
        )
    
    else:
        stmt = (
        select(
            Product.asin.label("product_asin"),
            Product.title,
            PriceSnapshot.price,
            PriceSnapshot.discount_pct,
            Keyword.name.label("keyword_name")
        )
        # 1. Tentukan kolom mana yang harus unik (tidak boleh duplikat ASIN)
        .distinct(Product.asin) 
        
        .join(PriceSnapshot, Product.id == PriceSnapshot.product_id)
        .join(ProductKeyword, Product.id == ProductKeyword.product_id)
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        .where(Keyword.name == keyword)
        
        # 2. WAJIB: Order by kolom distinct dulu, baru kolom pengurutnya
        .order_by(
            Product.asin, 
            desc(PriceSnapshot.scraped_at)
        )
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
            select(PriceSnapshot)
            .join(Product, Product.id == PriceSnapshot.product_id)
            .where(Product.asin == product_asin)
            .order_by(PriceSnapshot.scraped_at.asc())
        )
        
        # scalars() digunakan untuk mengambil objek PriceSnapshot utuh
        price_histories = session.scalars(stmt).all()
        
        return price_histories
    except Exception as e:
        print(f"Error pada query: {e}")
        return []

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
        .join(PriceSnapshot, Product.id == PriceSnapshot.product_id)
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
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today_start + timedelta(days=1)

    final = (
        select(subq)
        .where(subq.c.prev_price.isnot(None))
        .where(subq.c.scraped_at >= today_start)
        .where(subq.c.scraped_at < tomorrow)
    )

    result = session.execute(final).all()

    return result

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
                order_by=PriceSnapshot.scraped_at.asc()
            )
            .label("prev_price")
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
        
        .where(ranked.c.prev_price.isnot(None))
        .where(ranked.c.prev_price > 0)
        .where(ranked.c.price != ranked.c.prev_price)
        .where(ranked.c.scraped_at >= today_start)
        .where(ranked.c.scraped_at < tomorrow)
        
        .order_by(ranked.c.scraped_at.desc())
    )

    return session.execute(stmt).mappings().all()
    
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
        .where(ranked.c.prev_price > 0)
        .where(
            ((ranked.c.prev_price - ranked.c.price) / ranked.c.prev_price * 100)
            >= threshold_pct
        )
        .order_by(ranked.c.scraped_at.desc())
    )

    return session.execute(stmt).all()

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

def get_last_scraped_at():
    session = get_session()
    stmt = (
        select(func.date_trunc('second', ScrapingLog.started_at)).order_by(ScrapingLog.started_at.desc()).limit(1)
    )
    result = session.execute(stmt).scalar()
    session.close()
    return result

#-------------------- Keyword Grouping Queries

def get_all_keywords(session):
    stmt = select(Keyword)
    keywords = session.scalars(stmt).all()
    
    return keywords