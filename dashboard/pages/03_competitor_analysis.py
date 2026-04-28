import streamlit as st
import plotly.express as px

from services.data_loader import load_products, load_keywords
from utils.product_utils import get_keyword_options, filter_by_keyword
from utils.dataframe_builders import build_competitor_dataframe, build_display_table

st.set_page_config(page_title="Competitor Analysis", layout="wide")
st.title("📊 Competitor Analysis")

# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────

products = load_products()
keywords = load_keywords()

if not products:
    st.warning("There's no data. Search products first.")
    st.stop()

# ─────────────────────────────────────────────
# Filter
# ─────────────────────────────────────────────

selected_keyword = st.selectbox(
    "Filter by Keyword Group",
    get_keyword_options(keywords)
)

filtered_products = filter_by_keyword(products, selected_keyword)

if not filtered_products:
    st.info("No products found for this keyword group.")

df = build_competitor_dataframe(filtered_products)

# ─────────────────────────────────────────────
# Price Comparison Chart
# ─────────────────────────────────────────────
price_df = df.sort_values("Price", ascending=True)

fig_price = px.bar(
    price_df,
    x="Price",
    y="Product",
    orientation="h",
    title="Newest Price — sorted by lowest price",
)

fig_price.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
    yaxis={"categoryorder": "total ascending"},
)

st.plotly_chart(fig_price, width="stretch")


# ─────────────────────────────────────────────
# Discount Scatter Chart
# ─────────────────────────────────────────────

st.subheader("🔥 Discount Comparison")

fig_discount = px.scatter(
    df,
    x="Price",
    y="Discount",
    text="Brand",
    color="Category",
    size="Review Count",
    size_max=25,
    hover_data={
        "Product": True,
        "Brand": True,
        "Price": ":.2f",
        "Discount": ":.2f",
        "Review Count": True,
    },
    title="Right = More Expensive | Up = Higher Discount",
)

fig_discount.update_traces(textposition="top center")

avg_price = df["Price"].mean()
avg_discount = df["Discount"].mean()

fig_discount.add_vline(
    x=avg_price,
    line_dash="dash",
    line_color="gray",
)

fig_discount.add_hline(
    y=avg_discount,
    line_dash="dash",
    line_color="gray",
)

fig_discount.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
    yaxis_ticksuffix="%",
    legend_title="Category",
)

st.plotly_chart(fig_discount, width="stretch")


# ─────────────────────────────────────────────
# Full Table
# ─────────────────────────────────────────────

st.subheader("Complete Table")

display_df = build_display_table(df)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)