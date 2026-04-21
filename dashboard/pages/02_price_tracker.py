import streamlit as st
import plotly.express as px
import pandas as pd
from database.queries import get_session, get_all_products, get_price_history

st.set_page_config(page_title="Price Tracker", layout='wide')
st.title('Price Tracker')

session = get_session()

products = get_all_products(session)

if not products:
    st.warning("There's no data. Search Products first!")
    st.stop()

st.subheader('Newest Price')

all_products_rows = []
for i in products:
    change_text = '-'
    if i.change < 0:
        # Harga Turun
        change_text = f"↓ ${abs(i.change):,.2f}"
    elif i.change > 0:
        # Harga Naik
        change_text = f"↑ ${i.change:,.2f}"
    all_products_rows.append({
        'Image': i.image_url,
        'ASIN': i.asin,
        'Product': i.title,
        'Price': f'${i.price}',
        'Change': change_text,
        'Discount': f'{i.discount_pct:.2f}%' if i.discount_pct > 0 else '-',
        'Last Updated': i.scraped_at
    })
    
ap_df = pd.DataFrame(all_products_rows)
st.dataframe(
    ap_df,
    column_config={
        "Image": st.column_config.ImageColumn(
            "Product Image"
        )    
    }, 
    width='stretch', 
    hide_index=True
)

# ─── Chart history harga ─────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Price Trend")

product_options = {row["Product"]: row["ASIN"] for row in all_products_rows}
selected = st.selectbox("Choose Product", options=list(product_options.keys()))
selected_asin = product_options[selected]

selected_product = next((p for p in products if p.asin == selected_asin), None)

if selected_product:
    history = get_price_history(session, selected_product.asin)
    
    if len(history) > 1:
        hist_df = pd.DataFrame([{
            "Date": h.scraped_at,
            "Price": h.price,
        } for h in history])

        fig = px.line(
            hist_df, x="Date", y="Price",
            title=f"Price History — {selected[:50]}",
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
        st.info("There is not enough historical data for this product. Please run the scraper again in a few days.")

session.close()