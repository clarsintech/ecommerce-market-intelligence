import streamlit as st
import plotly.express as px

from services.data_loader import load_products, load_price_history
from utils.product_utils import get_product_options, find_product_by_asin
from utils.dataframe_builders import build_products_dataframe, build_history_dataframe

st.set_page_config(page_title="Price Tracker", layout='wide')
st.title('📈 Price Tracker')

products = load_products()

if not products:
    st.warning("There's no data. Search Products first!")
    st.stop()

# ─────────────────────────────────────────────
# Newest Price Table
# ─────────────────────────────────────────────

st.subheader('Newest Price')

products_df = build_products_dataframe(products)

st.dataframe(
    products_df,
    column_config={
        'Image': st.column_config.ImageColumn('Product Image'),
    },
    width="stretch",
    hide_index=True
)

# ─────────────────────────────────────────────
# Price Trend
# ─────────────────────────────────────────────

st.divider()
st.subheader("📈 Price Trend")

product_options = get_product_options(products)

selected_product_name = st.selectbox(
    "Choose Product",
    options=list(product_options.keys()),
)

selected_asin = product_options[selected_product_name]
selected_product = find_product_by_asin(products, selected_asin)

if selected_product:
    history = load_price_history(selected_product['asin'])

    if len(history) > 1:
        history_df = build_history_dataframe(history)

        fig = px.line(
            history_df,
            x="Date",
            y="Price",
            title=f"Price History — {selected_product['title'][:50]}",
            markers=True,
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_tickprefix="$",
        )

        st.plotly_chart(fig, width="stretch")
    else:
        st.info(
            "There is not enough historical data for this product. "
            "Please run the scraper again in a few days."
        )