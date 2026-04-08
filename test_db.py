import sqlite3

# create db file 
conn = sqlite3.connect("market_intel.db")
cursor = conn.cursor()

print("Koneksi berhasil! File market_intel.db telah dibuat.")

# create table for test
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY,
        asin TEXT UNIQUE,
        title TEXT,
        price REAL
    )
""")

# fill 1 data
cursor.execute("""
    INSERT OR IGNORE INTO products (asin, title, price)
    VALUES ('B08N5WRWNW', 'ErgoChair Pro', 499.0)
""")

conn.commit()

rows = cursor.execute("SELECT * FROM products").fetchall()
print(rows)

conn.close()