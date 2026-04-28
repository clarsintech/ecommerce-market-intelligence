def calculate_average_price(products):
    prices = [p['price'] for p in products if p['price'] is not None] 
    if not prices:
        return 0
    
    return sum(prices) / len(prices)

def get_keyword_options(keywords):
    return ['All'] + [keyword['name'] for keyword in keywords]
 
def get_product_options(products):
    return {
        f"{product['title'][:80]}": product['asin']
        for product in products
    }

def find_product_by_asin(products, asin):
    return next(
        (product for product in products if product['asin'] == asin),
        None
    )

def get_deal_category(row, median_price):
    if row["Discount"] >= 30:
        return "🔥 Best Deal"

    if row["Price"] <= median_price:
        return "💰 Budget"

    return "Normal"

def get_product_asin(product):
    return product['ASIN']

def filter_by_keyword(items, selected_keyword):
    if selected_keyword == 'All':
        return items
    
    return [
        item for item in items
        if item['keyword_name'] == selected_keyword
    ]
    