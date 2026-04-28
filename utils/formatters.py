
def format_currency(value):
    if value is None:
        return '-'
    
    return f'${value:,.2f}'

def format_change(value):
    if value is None:
        return "-"

    if value < 0:
        return f"↓ {format_currency(abs(value))}"

    if value > 0:
        return f"↑ {format_currency(value)}"

    return "-"

def format_discount(value):
    if not value or value <= 0:
        return "-"

    return f"{value:.2f}%"

def format_rating(product):
    rating = product.get("rating") or 0
    reviews = product.get("review_count") or 0
    is_prime = product.get("is_prime")

    try:
        stars = "⭐" * int(float(rating))
    except (TypeError, ValueError):
        stars = ""

    prime_badge = "🟡 **Prime**" if is_prime else ""

    return f"{stars} {rating} | {reviews} reviews | {prime_badge}"
