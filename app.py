import streamlit as st

from services.data_loader import load_latest_scraping_log
from utils.formatters import format_datetime

st.set_page_config(
    page_title="Amazon Market Intelligence",
    page_icon="📊",
    layout="wide",
)

latest_log = load_latest_scraping_log()

last_scraped = (
    format_datetime(latest_log['finished_at'])
    if latest_log
    else '-'
)

status = latest_log['status'] if latest_log else 'Unknown'

scraped_count = latest_log["products_scraped"] if latest_log else 0
failed_count = latest_log["products_failed"] if latest_log else 0

total = scraped_count + failed_count

success_rate = (
    scraped_count / total * 100
    if total > 0 else 0
)

st.title("📊 Amazon Market Intelligence")
st.markdown("Monitor competitor prices, detect product trends, make faster decisions.")

# st.markdown(f"*:grey[Last Updated: {last_scraped} | Status: {status}]*")

icon = "🟢" if status == "success" else "🔴"

st.caption(
    f"{icon} Last Updated: {last_scraped} | "
    f"{scraped_count} Products Scraped | "
    f"Success {success_rate:.0f}%"
)

st.divider()

    
pg = st.navigation([
    st.Page("dashboard/pages/01_dashboard.py", title="Dashboard", icon="🏠"),
    st.Page("dashboard/pages/02_price_tracker.py", title="Price Tracker", icon="📉"),
    st.Page("dashboard/pages/03_competitor_analysis.py", title="Competitor Analysis", icon="🎯"),
    st.Page("dashboard/pages/04_product_search.py", title="Product Search", icon="🔎")
])

pg.run()