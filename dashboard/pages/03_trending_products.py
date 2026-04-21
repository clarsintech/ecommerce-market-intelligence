import streamlit as st
import pandas as pd
import plotly.express as px
from database.queries import get_session, get_products_with_price_drop, get_latest_price_all

st.set_page_config(page_title="Trending Products", layout="wide")
st.title("🔥 Trending Products")

session = get_session()

# ─── Produk dengan harga turun ────────────────────────────────────────────────
st.subheader("Produk yang Harganya Turun Hari Ini")

price_drops = get_products_with_price_drop(session)

if not price_drops:
    st.info("Tidak ada perubahan harga hari ini, atau belum cukup data history.")
else:
    drop_rows = []
    for row in price_drops:
        if row.prev_price and row.price < row.prev_price:
            drop_pct = (row.prev_price - row.price) / row.prev_price * 100
            drop_rows.append({
                "Product ID": row.product_id,
                "Harga Sekarang": f"${row.price:.2f}",
                "Harga Sebelumnya": f"${row.prev_price:.2f}",
                "Turun": f"{drop_pct:.1f}%",
                "Waktu": row.scraped_at,
            })

    if drop_rows:
        drop_df = pd.DataFrame(drop_rows)
        st.dataframe(drop_df, width="stretch", hide_index=True)
    else:
        st.info("Tidak ada produk yang harganya turun hari ini.")

# ─── Overview semua produk ────────────────────────────────────────────────────
st.divider()
st.subheader("Overview Semua Produk")

latest = get_latest_price_all(session)

rows = []
for product, snapshot in latest:
    rows.append({
        "Produk": product.title[:50],
        "Brand": product.brand or "Unknown",
        "Harga": snapshot.price,
        "Diskon": snapshot.discount_pct or 0,
        "Stok": "Ada" if snapshot.is_in_stock else "Habis",
    })

df = pd.DataFrame(rows)

fig = px.bar(
    df.sort_values("Diskon", ascending=False),
    x="Produk", y="Diskon",
    color="Stok",
    color_discrete_map={"Ada": "#1DB954", "Habis": "#E74C3C"},
    title="Produk dengan diskon terbesar",
)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis_ticksuffix="%",
    xaxis_tickangle=-30,
)
st.plotly_chart(fig, width="stretch")

session.close()