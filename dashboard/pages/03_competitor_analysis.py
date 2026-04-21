import streamlit as st
import pandas as pd
import plotly.express as px
from database.queries import get_session, get_all_products, get_all_keywords

st.set_page_config(page_title="Competitor Analysis", layout="wide")
st.title("📊 Competitor Analysis")

session = get_session()

products_grouping = get_all_products(session)
keywords = get_all_keywords(session)

keyword_list = []
filtered_products = []

for i in keywords:
    keyword_list.append(i.name)
keyword_list.append('All')

selected_keyword = st.selectbox(
    "Filter by Keyword Group",
    keyword_list
)

if selected_keyword == "All":
    filtered_products = products_grouping
else:
    filtered_products = [
        p for p in products_grouping if p["name"] == selected_keyword
    ]
    filtered_products.sort(key=lambda x: x["price"])


if not products_grouping:
    st.warning("Belum ada data.")
    st.stop()

rows = []
for product in filtered_products:
    change_text = '-'
    if product.change < 0:
        # Harga Turun
        change_text = f"↓ ${abs(product.change):.2f}"
    elif product.change > 0:
        # Harga Naik
        change_text = f"↑ ${product.change:.2f}"
    rows.append({
        "Product": product.title[:50],
        "Brand": product.brand or "Unknown",
        "Price": product.price,
        "Change": change_text,
        "Discount": product.discount_pct or 0,
        "Review Count": product.review_count
        # "Prime": "Prime" if snapshot.is_prime else "Non-Prime",
        # "Stok": "Ada" if snapshot.is_in_stock else "Habis",
    })
    

df = pd.DataFrame(rows)

# ─── Bar chart perbandingan harga ────────────────────────────────────────────
st.subheader("📊 Price Comparison (Chart)")

fig = px.bar(
    df.sort_values("Price"),
    x="Price", y="Product",
    orientation="h",
    # color="Prime",
    # color_discrete_map={"Prime": "#FF9900", "Non-Prime": "#232F3E"},
    title="Newest Price — sorted by lowest price",
)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
)
st.plotly_chart(fig, width="stretch")

# ─── Scatter plot harga vs diskon ────────────────────────────────────────────
st.subheader("🔥 Discount Comparison")

# --- Tambahin kategori (biar meaningful) ---
def get_category(row):
    if row['Discount'] >= 30:
        return "🔥 Best Deal"
    elif row['Price'] <= df["Price"].median():
        return "💰 Budget"
    else:
        return "Normal"

df["Category"] = df.apply(get_category, axis=1)

# --- Scatter Plot ---
fig2 = px.scatter(
    df,
    x="Price",
    y="Discount",
    text="Brand",
    color="Category",
    size="Review Count",  # pastikan ada column ini
    size_max=25,
    hover_data={
        "Price": True,
        "Discount": True,
        "Brand": True,
        "Review Count": True,
    },
    title="👉 Right = More Expensive | Up = Higher Discount",
)

# --- Position text ---
fig2.update_traces(textposition="top center")

# --- Tambahin garis average ---
avg_price = df["Price"].mean()
avg_discount = df["Discount"].mean()

fig2.add_vline(
    x=avg_price,
    line_dash="dash",
    line_color="gray"
)

fig2.add_hline(
    y=avg_discount,
    line_dash="dash",
    line_color="gray"
)

# --- Styling ---
fig2.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_tickprefix="$",
    yaxis_ticksuffix="%",
    legend_title="Category",
)

st.plotly_chart(fig2, width="stretch")

# ─── Tabel lengkap ───────────────────────────────────────────────────────────
st.subheader("Tabel Lengkap")
df_table = df
df_table['Price'] = '$' + df_table['Price'].astype(str)
df_table['Discount'] = df_table['Discount'].apply(
    lambda x: f"{x}%" if x > 0 else "-"
)
st.dataframe(df_table, width="stretch", hide_index=True)

session.close()