import asyncio
import sys
import os

# Menambahkan path folder utama ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# print("Current Working Directory:", os.getcwd())
# print("System Path:", sys.path)

import streamlit as st
import pandas as pd
import plotly.express as px
import io

from pipeline.tasks import process_task
from database.queries import get_session, get_all_keywords, get_price_drop_products, get_all_products, get_all_products_with_grouping, get_biggest_product_discount

scrape_clicked = st.button("Get New Price", type="primary")

if scrape_clicked:
    with st.spinner(f'Update product prices...'):
        # Pakai async version dari Streamlit
        results = asyncio.run(
            process_task()
        )
    if not results:
        st.error("No Products to scrape!")
        st.stop()

    st.success(f"Finished scraped new {results} products prices!")
    st.divider()

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("🔍 Dashboard")

session = get_session()
keywords = get_all_keywords(session)
latest = get_price_drop_products(session)
products = get_all_products(session)
products_grouping = get_all_products_with_grouping(session)
discount_product = get_biggest_product_discount(session)


# ____________Summary_________________________________________________________

keyword_list = []
keyword_list.append('All')

for i in keywords:
    keyword_list.append(i.name)

selected_keyword = st.selectbox(
    "Filter by Keyword Group",
    keyword_list
)

price_drops_today = 0
if selected_keyword == "All":
    filtered_products = products_grouping
    price_drops_today = len(latest)
else:
    filtered_products = [
        p for p in products_grouping if p["keyword_name"] == selected_keyword
    ]
    price_drops_today = len([
        p for p in latest if p['keyword_name'] == selected_keyword
    ])
    
total_products_grouping = len(filtered_products)

st.subheader(f"🏠 Overview — {selected_keyword}")

avg_price = (
    sum(p["price"] for p in filtered_products if p["price"]) 
    / total_products_grouping
) if total_products_grouping > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Watchlists", total_products_grouping)

with col2:
    st.metric("Average Price", f"${avg_price:.2f}")

with col3:
    st.metric("Price Drops Today", f'{price_drops_today} Items')

# ─── Tabel harga terbaru semua produk ────────────────────────────────────────
st.subheader("🔻Price Drops Today")

if not latest:
    st.warning("There's no data. Scrape first.")
    st.stop()

rows = []
for product in latest:
    diff = product.price - product.prev_price
    change = ''
    if diff < 0:
        # Harga Turun
        change = f"↓ ${abs(diff):,.2f}"
    elif diff > 0:
        # Harga Naik
        change = f"↑ ${diff:,.2f}"
    else:
        # Harga Tetap
        change = '-'
    rows.append({
        "ASIN": product.asin,
        "Product": product.title,
        "Brand": product.brand,
        "Price": f"${product.price:.2f}",
        "Change": change,
        # "Harga Asli": f"USD{snapshot.original_price:.2f}" if snapshot.original_price else "-",
        # "Diskon": f"{snapshot.discount_pct:.1f}%" if snapshot.discount_pct else "-",
        # "Prime": "✅" if snapshot.is_prime else "❌",
        "Last Updated": product.scraped_at,
        "In Stock": "✅" if product.is_in_stock else "❌",
    })
 
df = pd.DataFrame(rows)
st.dataframe(df, width='stretch', hide_index=True)

# df_export = df.copy()
# df_export["In Stock"] = df_export["In Stock"].replace({"Ada": "In Stock", "Habis": "Out of Stock"})

# # Convert df ke CSV
# csv_buffer = io.StringIO()
# df_export.to_csv(csv_buffer, index=False)
# csv_data = csv_buffer.getvalue()

# st.download_button(
#     label="⬇️ Download CSV",
#     data=csv_data,
#     file_name="price_tracker.csv",
#     mime="text/csv",
# )

# ─── Tabel harga diskon terbanyak (1 produk aja) ────────────────────────────────────────
st.subheader("🔥 Biggest Discounts Today")

if not discount_product:
    st.warning("There's no data.")
    st.stop()

dp_row = []
dp_row.append({
    "ASIN": discount_product.asin,
    "Product": discount_product.title,
    "Brand": discount_product.brand,
    "Price": f"${discount_product.prev_price:.2f} → ${discount_product.price:.2f}",
    "Discount": f'({discount_product.discount}%)',
    "Last Updated": product.scraped_at,
})
df_discount = pd.DataFrame(dp_row)
st.dataframe(df_discount, width='stretch', hide_index=True)

session.close()