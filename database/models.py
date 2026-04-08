from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

def init_db(db_path=None):
    from config.settings import DATABASE_URL
    
    # Kalau db_path dikasih, pakai SQLite. Kalau tidak, pakai DATABASE_URL dari settings
    url = f"sqlite:///{db_path}" if db_path else DATABASE_URL
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    print("✅ Database dan all tables created successfully!")
    return engine

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    asin       = Column(String(20), unique=True, nullable=False)
    title      = Column(String(500), nullable=False)
    brand      = Column(String(200))
    category   = Column(String(200))
    image_url  = Column(Text)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    price_history = relationship("PriceSnapshot", back_populates="product")

class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    product_id     = Column(Integer, ForeignKey("products.id"), nullable=False)
    price          = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_pct   = Column(Float)
    is_prime       = Column(Boolean, default=False)
    is_in_stock    = Column(Boolean, default=True)
    rating         = Column(Float)
    review_count   = Column(Float)
    scraped_at     = Column(DateTime, default=datetime.now())

    product = relationship("Product", back_populates="price_history")

class ScrapingLog(Base): # jadi ini untuk scraping harian, atau per sesi, jadi jumlah scrape nya banyak
    __tablename__ = "scraping_logs"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    status           = Column(String(20))
    products_scraped = Column(Integer, default=0) # isinya berapa produk yang udah berhasil di scrape
    products_failed  = Column(Integer, default=0)
    # isinya berapa produk yang gagal di scape
    error_message    = Column(Text)
    started_at       = Column(DateTime, default=datetime.utcnow)
    finished_at      = Column(DateTime)

def init_db(db_path="market_intel.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    print("✅ Database dan all tables created sucessfully!")
    return engine

if __name__ == "__main__":
    init_db()