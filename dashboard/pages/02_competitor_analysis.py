import streamlit as st
import pandas as pd
import plotly.express as px
from database.queries import get_engine, get_session, get_latest_price_all

st.set_page_config(page_title="Competitor Analysis", layout="wide")
st.title("🔍 Competitor Analysis")

engine = get_engine()
session = get_session(engine)

latest = get_latest_price_all(session)

if not latest:
    st.warning("Belum ada data.")
    st.stop()

rows = []
for product, snapshot in latest:
    rows.append({
        "Produk": product.title[:50],
        "Brand": product.brand or "Unknown",
        "Harga": snapshot.price,
        "Diskon": snapshot.discount_pct or 0,
        "Prime": "Prime" if snapshot.is_prime else "Non-Prime",
        "Stok": "Ada" if snapshot.is_in_stock else "Habis",
    })

df = pd.DataFrame(rows)

# ─── Bar chart perbandingan harga ────────────────────────────────────────────
st.subheader("Perbandingan Harga Antar Produk")

fig = px.bar(
    df.sort_values("Harga"),
    x="Harga", y="Produk",
    orientation="h",
    color="Prime",
    color_discrete_map={"Prime": "#FF9900", "Non-Prime": "#232F3E"},
    title="Harga saat ini — diurutkan dari termurah",
)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
)
st.plotly_chart(fig, width="stretch")

# ─── Scatter plot harga vs diskon ────────────────────────────────────────────
st.subheader("Harga vs Diskon")

fig2 = px.scatter(
    df,
    x="Harga", y="Diskon",
    text="Brand",
    color="Prime",
    color_discrete_map={"Prime": "#FF9900", "Non-Prime": "#232F3E"},
    title="Semakin kanan = mahal, semakin atas = diskon besar",
    size_max=20,
)
fig2.update_traces(textposition="top center")
fig2.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
    yaxis_ticksuffix="%",
)
st.plotly_chart(fig2, width='stretch')

# ─── Tabel lengkap ───────────────────────────────────────────────────────────
st.subheader("Tabel Lengkap")
st.dataframe(df, width="stretch", hide_index=True)

session.close()