import pandas as pd

from utils.formatters import (
    format_currency,
    format_change,
    format_discount
)
from utils.product_utils import get_deal_category

def build_price_drop_dataframe(products):
    rows = []

    for product in products:
        diff = product['price'] - product['prev_price']

        if diff < 0:
            change = f"↓ {format_currency(abs(diff))}"
        elif diff > 0:
            change = f"↑ {format_currency(diff)}"
        else:
            change = "-"

        rows.append({
            "ASIN": product['asin'],
            "Product": product['title'],
            "Brand": product['brand'],
            "Price": format_currency(product['price']),
            "Change": change,
            "Last Updated": product['scraped_at'],
            "In Stock": "✅" if product['is_in_stock'] else "❌",
        })

    return pd.DataFrame(rows)

def build_discount_dataframe(product):
    if not product:
        return pd.DataFrame()

    return pd.DataFrame([{
        "ASIN": product['asin'],
        "Product": product['title'],
        "Brand": product['brand'],
        "Price": f"{format_currency(product['prev_price'])} → {format_currency(product['price'])}",
        "Discount": f"${product['discount']:.2f}",
        "Last Updated": product['scraped_at'],
    }])

def build_products_dataframe(products):
    rows = []

    for product in products:
        rows.append({
            "Image": product['image_url'],
            "ASIN": product['asin'],
            "Product": product['title'],
            "Price": format_currency(product['price']),
            "Change": format_change(product['change']),
            "Discount": format_discount(product['discount_pct']),
            "Last Updated": product['scraped_at'],
        })

    return pd.DataFrame(rows)

def build_history_dataframe(history):
    return pd.DataFrame([{
        "Date": item['scraped_at'],
        "Price": item['price'],
    } for item in history])

def build_competitor_dataframe(products):
    rows = []

    for product in products:
        rows.append({
            "Product": product['title'], #[:50]
            "Brand": product['brand'] or "Unknown",
            "Price": product['price'] or 0,
            "Change": format_change(product['change']),
            "Discount": product['discount_pct'] or 0,
            "Review Count": product['review_count'] or 0,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    median_price = df["Price"].median()
    df["Category"] = df.apply(
        lambda row: get_deal_category(row, median_price),
        axis=1,
    )

    return df


def build_display_table(df):
    table_df = df.copy()

    table_df["Price"] = table_df["Price"].apply(format_currency)
    table_df["Discount"] = table_df["Discount"].apply(format_discount)

    return table_df

def build_summary_dataframe(results):
    return pd.DataFrame([{
        "ASIN": product["ASIN"],
        "Product": product["title"][:80] if product["title"] else "-",
        "Price": format_currency(product["price"]) if product["price"] else "N/A",
        "Rating": product["rating"] or 0,
        "Reviews": product["review_count"] or 0,
        "Prime": "✅" if product["is_prime"] else "❌",
    } for product in results])