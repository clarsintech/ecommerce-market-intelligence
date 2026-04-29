import asyncio
import sys
import os

# Menambahkan path folder utama ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# print("Current Working Directory:", os.getcwd())
# print("System Path:", sys.path)

import streamlit as st
from utils.product_utils import calculate_average_price, get_keyword_options, filter_by_keyword
from utils.dataframe_builders import build_discount_dataframe, build_price_drop_dataframe
from utils.formatters import format_currency
from services.data_loader import (
    load_discount,
    load_keywords,
    load_price_drop,
    load_products,
)

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("🔍 Dashboard")


# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────

keywords = load_keywords()
price_drops = load_price_drop()
products = load_products()
discount_product = load_discount() 

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
filtered_price_drops = filter_by_keyword(price_drops, selected_keyword)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────

st.subheader(f"🏠 Overview — {selected_keyword}")

total_watchlists = len(filtered_products)
avg_price = calculate_average_price(filtered_products)
price_drops_today = len(filtered_price_drops)

col1, col2, col3 = st.columns(3)

col1.metric("Total Watchlists", total_watchlists)
col2.metric("Average Price", format_currency(avg_price))
col3.metric("Price Drops Today", f'{price_drops_today} Items')

# ─────────────────────────────────────────────
# Price Drops Table
# ─────────────────────────────────────────────

st.subheader("🔄 Price Changes Today")

if not filtered_price_drops:
    st.info("No price drops found for this keyword.")
else:
    df_price_drops = build_price_drop_dataframe(filtered_price_drops)
    st.dataframe(df_price_drops, width="stretch", hide_index=True)


# ─────────────────────────────────────────────
# Biggest Discount Table
# ─────────────────────────────────────────────

st.subheader("🔥 Biggest Discount Today")

if not discount_product:
    st.info("No discount data available.")
else:
    df_discount = build_discount_dataframe(discount_product)
    st.dataframe(df_discount, width="stretch", hide_index=True)