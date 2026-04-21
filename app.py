import streamlit as st
from database.queries import get_last_scraped_at

last_scraping_log = get_last_scraped_at()

st.set_page_config(
    page_title="Amazon Market Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Amazon Market Intelligence")
st.markdown("Monitor competitor prices, detect product trends, make faster decisions.")

st.markdown(f"*:grey[Last Updated: {last_scraping_log}]*")
st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
# st.columns(5)

# with col1:
#     st.page_link("dashboard/pages/01_price_tracker.py", label="📈 Price Tracker")
#     st.caption("Pantau perubahan harga harian")

# with col2:
#     st.page_link("dashboard/pages/02_competitor_analysis.py", label="🔍 Competitor Analysis")
#     st.caption("Bandingkan harga vs kompetitor")

# with col3:
#     st.page_link("dashboard/pages/03_trending_products.py", label="🔥 Trending Products")
#     st.caption("Deteksi produk yang naik daun")
    
# with col4:
#     st.page_link("dashboard/pages/04_price_alerts.py", label="🔥 Price Alerts")
#     st.caption("Deteksi produk yang naik daun")
    
# with col5:
#     st.page_link("dashboard/pages/05_review_rating.py", label="🔥 Review Rating")
#     st.caption("Deteksi produk yang naik daun")
    
pg = st.navigation([
    st.Page("dashboard/pages/01_dashboard.py", title="Dashboard", icon="🏠"),
    st.Page("dashboard/pages/02_price_tracker.py", title="Price Tracker", icon="📉"),
    st.Page("dashboard/pages/03_competitor_analysis.py", title="Competitor Analysis", icon="🎯"),
    # st.Page("dashboard/pages/04_price_alerts.py", title="Price Alerts"),
    # st.Page("dashboard/pages/05_review_rating.py", title="Review Rating"),
    st.Page("dashboard/pages/04_product_search.py", title="Product Search", icon="🔎")
])

pg.run()