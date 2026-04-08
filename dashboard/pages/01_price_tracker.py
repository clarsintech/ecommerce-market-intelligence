import sys
import os


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px
import io
from database.queries import get_engine, get_session, get_all_products, get_price_history, get_latest_price_all

st.set_page_config(page_title="Price Tracker", layout="wide")
st.title("📈 Price Tracker")

engine = get_engine()
session = get_session(engine)

# ─── Tabel harga terbaru semua produk ────────────────────────────────────────
st.subheader("Harga Terbaru")

latest = get_latest_price_all(session)

if not latest:
    st.warning("Belum ada data. Jalankan scraper dulu.")
    st.stop()

rows = []
for product, snapshot in latest:
    rows.append({
        "ASIN": product.asin,
        "Produk": product.title[:60],
        "Brand": product.brand,
        "Harga": f"IDR{snapshot.price:.2f}",
        "Harga Asli": f"IDR{snapshot.original_price:.2f}" if snapshot.original_price else "-",
        "Diskon": f"{snapshot.discount_pct:.1f}%" if snapshot.discount_pct else "-",
        "Prime": "✅" if snapshot.is_prime else "❌",
        "Stok": "Ada" if snapshot.is_in_stock else "Habis",
    })
 
df = pd.DataFrame(rows)
st.dataframe(df, width='stretch', hide_index=True)


df_export = df.copy()
df_export["Prime"] = df_export["Prime"].replace({"✅": "Yes", "❌": "No"})
df_export["Stok"] = df_export["Stok"].replace({"Ada": "In Stock", "Habis": "Out of Stock"})

# Convert df ke CSV
csv_buffer = io.StringIO()
df_export.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name="price_tracker.csv",
    mime="text/csv",
)

# ─── Chart history harga ─────────────────────────────────────────────────────
st.divider()
st.subheader("Riwayat Harga")

product_options = {row["Produk"]: row["ASIN"] for row in rows}
selected = st.selectbox("Pilih produk", options=list(product_options.keys()))
selected_asin = product_options[selected]

products = get_all_products(session)
selected_product = next((p for p in products if p.asin == selected_asin), None)

if selected_product:
    history = get_price_history(session, selected_product.id)
    
    if len(history) > 1:
        hist_df = pd.DataFrame([{
            "Tanggal": h.scraped_at,
            "Harga": h.price,
        } for h in history])

        fig = px.line(
            hist_df, x="Tanggal", y="Harga",
            title=f"Riwayat Harga — {selected[:50]}",
            markers=True,
            color_discrete_sequence=["#FF6B35"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_tickprefix="$",
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Belum cukup data history untuk produk ini. Jalankan scraper beberapa hari lagi.")



session.close()