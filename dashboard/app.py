import streamlit as st
# from pipeline.tasks import process_task

st.set_page_config(
    page_title="Amazon Market Intelligence",
    page_icon="📊",
    layout="wide",
)

# process_task()

st.title("📊 Amazon Market Intelligence")
st.caption("Pantau harga kompetitor, deteksi trending produk, ambil keputusan lebih cepat.")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/01_price_tracker.py", label="📈 Price Tracker")
    st.caption("Pantau perubahan harga harian")

with col2:
    st.page_link("pages/02_competitor_analysis.py", label="🔍 Competitor Analysis")
    st.caption("Bandingkan harga vs kompetitor")

with col3:
    st.page_link("pages/03_trending_products.py", label="🔥 Trending Products")
    st.caption("Deteksi produk yang naik daun")