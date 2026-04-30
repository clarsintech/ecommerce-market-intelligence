from bs4 import BeautifulSoup

from utils.scraper_cleaners import (
    clean_price, 
    parse_bool, 
    extract_brand, 
    clean_rating, 
    clean_review_count
)

def make_soup(html):
    if not html:
        return None

    return BeautifulSoup(html, 'lxml')

def get_text(element):
    if not element:
        return None
    
    return element.get_text(strip=True)

def get_attr(element, attr):
    if not element:
        return None

    return element.get(attr)

# ─────────────────────────────────────────────
# Product Detail Parser
# ─────────────────────────────────────────────

def parse_title(soup):
    return get_text(soup.select_one('#productTitle'))

def parse_asin(soup):
    asin_element = soup.select_one('#ASIN')
    return get_attr(asin_element, "value")

def parse_category(soup):
    return get_text(soup.select_one('#wayfinding-breadcrumbs_feature_div'))

def parse_image_url(soup):
    image_element = soup.select_one('#landingImage')
    return get_attr(image_element, "src")

def parse_stock_status(soup):
    out_of_stock = soup.select_one("#outOfStock")
    return out_of_stock is None

def parse_price(soup):
    selectors = [
        ".apex-pricetopay-value span[aria-hidden='true']",
        ".a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if not price_element:
            return 0
        price_text = get_text(price_element)

        if price_text:
            return clean_price(price_text)

    return 0

def parse_prime_status(soup):
    prime_element = soup.select_one("#usePrimeHandler")
    prime_value = get_attr(prime_element, "value")

    return parse_bool(prime_value)


def parse_brand(soup):
    # Case 1: ambil text dari <a> di dalam premiumBylineInfo_feature_div
    brand_element = soup.select_one("#premiumBylineInfo_feature_div a")

    if brand_element:
        return extract_brand(get_text(brand_element))

    # Case 2: fallback ke productOverview_feature_div
    # row pertama, kolom kedua = tr pertama > td kedua
    brand_element = soup.select_one(
        "#productOverview_feature_div table tbody tr:first-child td:nth-child(2)"
    )

    if brand_element:
        return extract_brand(get_text(brand_element))

    return None


def parse_product_rating(soup):
    rating_element = soup.select_one("#acrPopover")
    rating_text = get_attr(rating_element, "title")

    return clean_rating(rating_text)


def parse_product_review_count(soup):
    review_element = soup.select_one("#acrCustomerReviewText")
    review_text = get_text(review_element)

    return clean_review_count(review_text)

def process_html(response):
    soup = make_soup(response)

    if not soup:
        return None

    title = parse_title(soup)

    if not title:
        return None

    is_in_stock = parse_stock_status(soup)

    price = 0
    original_price = 0

    if is_in_stock:
        price = parse_price(soup)
        original_price = parse_original_price(soup, price)

        if price <= 0:
            is_in_stock = False

    return {
        "ASIN": parse_asin(soup),
        "title": title,
        "brand": parse_brand(soup),
        "category": parse_category(soup),
        "image_url": parse_image_url(soup),
        "price": price,
        "original_price": original_price,
        "is_in_stock": is_in_stock,
        "is_prime": parse_prime_status(soup),
        "rating": parse_product_rating(soup),
        "review_count": parse_product_review_count(soup),
    }
    
# ─────────────────────────────────────────────
# Search Result Parser
# ─────────────────────────────────────────────

def is_sponsored_item(item) -> bool:
    title_recipe = item.find("div", attrs={"data-cy": "title-recipe"})

    if not title_recipe:
        return False

    return "Sponsored" in title_recipe.get_text(strip=True)


def parse_search_title(item) -> str | None:
    title_recipe = item.find("div", attrs={"data-cy": "title-recipe"})

    if not title_recipe:
        return None

    return title_recipe.get_text(strip=True)


def parse_search_asin(item) -> str | None:
    return item.get("data-asin")


def parse_search_image(item) -> str | None:
    image = item.find("img", class_="s-image")
    return get_attr(image, "src")


def parse_search_rating(item) -> float:
    review_rating_slot = item.find("i", attrs={"data-cy": "reviews-ratings-slot"})
    rating_text = get_text(review_rating_slot)

    return clean_rating(rating_text)


def parse_search_review_count(item) -> int:
    review_node = item.find("div", attrs={"data-csa-c-slot-id": "alf-reviews"})

    if not review_node:
        return 0

    link = review_node.find("a")
    review_text = get_attr(link, "aria-label")

    return clean_review_count(review_text)


def parse_search_price(item) -> float:
    price_node = item.select_one("span.a-price")

    if not price_node:
        return 0

    offscreen = price_node.select_one("span.a-offscreen")
    price_text = get_text(offscreen)

    return clean_price(price_text)


def parse_original_price(item, current_price) -> float:
    price_node = item.select_one('#corePriceDisplay_desktop_feature_div')

    original_price_node = price_node.find(
        "span",
        class_="a-text-price",
        attrs={
            "data-a-strike": "true",
        },
    )

    if not original_price_node:
        return current_price

    hidden_span = original_price_node.find("span", attrs={"aria-hidden": "true"})
    price_text = get_text(hidden_span)

    return clean_price(price_text)


def parse_search_prime_status(item) -> bool:
    prime_recipe = item.find("div", attrs={"data-cy": "price-recipe"})

    if not prime_recipe:
        return False

    return "Prime" in prime_recipe.get_text(strip=True)


def parse_search_item(item) -> dict | None:
    if is_sponsored_item(item):
        return None
    asin = parse_search_asin(item)
    title = parse_search_title(item)
    price = parse_search_price(item)

    if not asin or not title or price <= 0:
        return None
    return {
        "ASIN": asin,
        "title": title,
        "image_url": parse_search_image(item),
        "rating": parse_search_rating(item),
        "review_count": parse_search_review_count(item),
        "price": price,
        "is_prime": parse_search_prime_status(item),
    }


def process_search_results(response: str | None, max_results: int) -> list[dict]:
    soup = make_soup(response)

    if not soup:
        return []

    items = soup.find_all("div", {"role": "listitem"})
    results = []

    for item in items:
        product = parse_search_item(item)

        if not product:
            continue

        results.append(product)
        if len(results) >= max_results:
            break

    return results