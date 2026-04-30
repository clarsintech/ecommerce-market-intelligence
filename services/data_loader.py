import streamlit as st

from database.queries import (
    get_session, 
    get_latest_products,
    get_all_keywords, 
    get_price_drop_products, 
    get_biggest_product_discount, 
    get_price_history,
    get_last_scraped_at    
)

def run_query(fn):
    session = get_session()
    try:
        return fn(session)
    finally:
        session.close()
        
@st.cache_data(ttl=600)
def load_products():
    products = run_query(get_latest_products)
    
    if not products:
        return None
    
    return [dict(row) for row in products]


@st.cache_data(ttl=600)
def load_keywords():
    keywords = run_query(get_all_keywords)
    return [
        {
            'id': k.id,
            'name': k.name
        }
        for k in keywords
    ]

@st.cache_data(ttl=600)
def load_price_drop():
    products = run_query(get_price_drop_products)
    
    if not products:
        return None
    
    return [dict(row) for row in products]

@st.cache_data(ttl=600)
def load_discount():
    product = run_query(get_biggest_product_discount)
    
    if not product:
        return None
    
    return dict(product)

@st.cache_data(ttl=600)
def load_price_history(asin):
    
    session = get_session()
    try:
        price_histories = get_price_history(session, asin)
        return [dict(row) for row in price_histories]
    finally:
        session.close()
        
@st.cache_data(ttl=600)
def load_latest_scraping_log():
    log = run_query(get_last_scraped_at)
    
    if not log:
        return None

    return dict(log)