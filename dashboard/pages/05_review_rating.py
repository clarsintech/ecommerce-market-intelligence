import streamlit as st
import pandas as pd
import plotly.express as px
from database.queries import get_engine, get_session, get_all_products, get_products_rating_and_review, get_price_history

st.set_page_config(page_title="Review & Rating Tracker", layout="wide")
st.title("⭐ Review & Rating Tracker")
st.caption("Pantau naik turunnya rating dan jumlah review kompetitor")

engine = get_engine()
session = get_session(engine)

products = get_all_products(session)

if not products:
    st.warning("Belum ada data. Jalankan scraper dulu.")
    st.stop()

# ─── Overview semua produk ────────────────────────────────────────────────────
st.subheader("Overview Rating Semua Produk")

rows = []
for p in products:
    history = get_price_history(session, p.id)
    if history:
        latest = history[-1]  # ambil yang terbaru
        rows.append({
            "Produk": p.title[:50],
            "Brand": p.brand or "-",
            "Rating": latest.rating or 0,
            "Review Count": latest.review_count or 0,
            "ASIN": p.asin,
        })

if not rows:
    st.info("Belum ada data rating.")
    st.stop()

df = pd.DataFrame(rows)

# Bar chart rating
fig = px.bar(
    df.sort_values("Rating", ascending=False),
    x="Produk", y="Rating",
    color="Rating",
    color_continuous_scale="RdYlGn",
    title="Rating per Produk",
    text="Rating",
)
fig.update_traces(textposition="outside")
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis_range=[0, 5],
    xaxis_tickangle=-30,
    coloraxis_showscale=False,
)
st.plotly_chart(fig, width="stretch")

# Bar chart review count
fig2 = px.bar(
    df.sort_values("Review Count", ascending=False),
    x="Produk", y="Review Count",
    color="Review Count",
    color_continuous_scale="Blues",
    title="Jumlah Review per Produk",
    text="Review Count",
)
fig2.update_traces(textposition="outside")
fig2.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickangle=-30,
    coloraxis_showscale=False,
)
st.plotly_chart(fig2, width="stretch")

# ─── History rating per produk ────────────────────────────────────────────────
st.divider()
st.subheader("History Rating & Review")

product_options = {p.title[:50]: p.id for p in products}
selected = st.selectbox("Pilih produk", options=list(product_options.keys()))
selected_id = product_options[selected]

rating_history = get_products_rating_and_review(session, selected_id)

if len(rating_history) > 1:
    hist_df = pd.DataFrame([{
        "Tanggal": row.scraped_at,
        "Rating": row.rating,
        "Review Count": row.review_count,
    } for row in rating_history])

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.line(
            hist_df, x="Tanggal", y="Rating",
            title="Trend Rating",
            markers=True,
            color_discrete_sequence=["#F4C430"],
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_range=[0, 5],
        )
        st.plotly_chart(fig3, width="stretch")

    with col2:
        fig4 = px.line(
            hist_df, x="Tanggal", y="Review Count",
            title="Trend Jumlah Review",
            markers=True,
            color_discrete_sequence=["#4A90E2"],
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig4, width="stretch")

else:
    st.info("Belum cukup data history. Jalankan scraper beberapa hari lagi untuk lihat trendnya.")

# ─── Tabel lengkap ────────────────────────────────────────────────────────────
st.divider()
st.subheader("Tabel Lengkap")
st.dataframe(df, width="stretch", hide_index=True)

session.close()