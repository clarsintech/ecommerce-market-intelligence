import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import io

from pipeline.tasks import process_search_tasks_async, save_watchlist_products
from utils.product_utils import get_product_asin
from utils.formatters import format_currency, format_rating
from utils.dataframe_builders import build_summary_dataframe

st.set_page_config(page_title="Product Search", layout="wide")
st.title("🔍 Product Search")
st.caption("Search for products on Amazon and instantly monitor prices")

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────

def init_session_state() -> None:
    if "selected_asins" not in st.session_state:
        st.session_state.selected_asins = set()

    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    if "success_message" not in st.session_state:
        st.session_state.success_message = None
        
    if "saved_asins" not in st.session_state:
        st.session_state.saved_asins = set()

def clear_checkbox_states():
    for key in list(st.session_state.keys()):
        if key.startswith('check_'):
            del st.session_state[key]

def reset_search_state():
    st.session_state.selected_asins = set()
    st.session_state.search_results = []
    st.session_state.success_message = None
    clear_checkbox_states()

init_session_state()

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def toggle_asin(asin: str) -> None:
    if asin in st.session_state.saved_asins:
        st.session_state.selected_asins.discard(asin)
        return
    
    checkbox_key = f"check_{asin}"

    if st.session_state.get(checkbox_key):
        st.session_state.selected_asins.add(asin)
    else:
        st.session_state.selected_asins.discard(asin)

def change_all(results, select):
    available_asins = {
        get_product_asin(product)
        for product in results
        if get_product_asin(product) not in st.session_state.saved_asins
    }

    for product in results:
        asin = get_product_asin(product)
        if asin not in st.session_state.saved_asins:
            st.session_state[f'check_{asin}'] = select

    st.session_state.selected_asins = available_asins if select else set()
    
def render_product_card(product):
    asin = get_product_asin(product)
    is_saved = asin in st.session_state.saved_asins

    col_check, col_img, col_info, col_price = st.columns([0.4, 1, 3, 1.5])
    

    with col_check:
        checkbox_key = f'check_{asin}'
    
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = asin in st.session_state.selected_asins
            
        st.checkbox(
            "Select",
            key=checkbox_key,
            on_change=toggle_asin,
            args=(asin,),
            disabled=is_saved,
            label_visibility="collapsed",
        )

    with col_img:
        image_url = product['image_url']
        if image_url:
            st.image(image_url, width=80)
        else:
            st.caption("No image")
            
    with col_info:
        title = product['title'] or "*No Title*"
        st.markdown(f"**{title}**")

        if is_saved:
            st.success("✅ Added to Watchlist")
        else:
            st.caption(format_rating(product))

    with col_price:
        price = product["price"]
        price_display = format_currency(price) if price else "N/A"
        st.metric("Price", price_display)

    st.divider()

def render_search_results(results):
    st.subheader("Search Results")
    st.caption("Tick the products you want to add to your watchlist")

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 3])

    with ctrl_col1:
        st.button(
            "Select All",
            on_click=change_all,
            args=(results, True),
            use_container_width=True,
        )

    with ctrl_col2:
        st.button(
            "Clear",
            on_click=change_all,
            args=(results, False),
            use_container_width=True,
        )

    with ctrl_col3:
        st.caption(f"#### **{len(st.session_state.selected_asins)}** product(s) selected")

    st.divider()

    for product in results:
        render_product_card(product)

def render_summary_table(results):
    st.divider()
    st.subheader("Results Summary")

    df = build_summary_dataframe(results)

    st.dataframe(df, width="stretch", hide_index=True)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    keyword = st.session_state.search_keyword or "results"

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"search_{keyword}.csv",
        mime="text/csv",
    )


# ─────────────────────────────────────────────
# Search Input
# ─────────────────────────────────────────────

with st.container():
    col1, col2, col3 = st.columns([6, 2, 1])

    with col1:
        keyword = st.text_input(label="Search Product", placeholder="🔍 Search Product...", label_visibility="collapsed")

    with col2:
        max_results = st.selectbox("No of Results", [5, 10, 20], index=1, label_visibility="collapsed")

    with col3:
        search_clicked = st.button("Search", width='stretch')

# ─────────────────────────────────────────────
# Search Action
# ─────────────────────────────────────────────

if search_clicked:
    if not keyword.strip():
        st.warning("Enter the product keyword first.")
        st.stop()

    reset_search_state()

    with st.spinner(f'Searching "{keyword}" on Amazon...'):
        results = asyncio.run(
            process_search_tasks_async(
                keyword=keyword.strip(),
                max_results=max_results,
            )
        )

    if not results:
        st.error("No results found. Try another keyword.")
        st.stop()

    st.session_state.search_results = results
    st.session_state.search_keyword = keyword.strip()

    st.success(f"{len(results)} products found for keyword **{keyword}**")

# ─────────────────────────────────────────────
# Success Message
# ─────────────────────────────────────────────

if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = None

# ─────────────────────────────────────────────
# Render Results
# ─────────────────────────────────────────────

results = st.session_state.search_results

if results:
    render_search_results(results)

    if st.button("➕ Add to Watchlist!", type="primary", use_container_width=True):
        final_asins = [
            asin for asin in st.session_state.selected_asins
            if asin not in st.session_state.saved_asins
        ]
        
        if not final_asins:
            st.warning('Please select at least 1 new product.')
        else:
            with st.spinner("Saving to database..."):
                keyword_to_save = st.session_state.search_keyword

                success_count = asyncio.run(
                    save_watchlist_products(final_asins, keyword_to_save)
                )

            if success_count:
                saved_now = set(final_asins)

                st.session_state.saved_asins.update(saved_now)
                st.session_state.selected_asins.difference_update(saved_now)

                for asin in saved_now:
                    st.session_state.pop(f'check_{asin}', None)

                st.session_state.success_message = (
                    f"✅ Success! {success_count} products have entered the watchlist."
                )

                st.rerun()
            else:
                st.error("Failed to save to database.")

    render_summary_table(results)