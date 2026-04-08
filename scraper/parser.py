from bs4 import BeautifulSoup
from scraper.utils import clean_price, parse_bool, extract_brand, clean_rating, clean_review_count

def process_html(response):
    
    if response:
        soup = BeautifulSoup(response, 'lxml')
    else:
        print('gada produk')
        return
    
    
    title_element = soup.select_one('#productTitle')
    
    # ✅ Tambahkan ini — kalau title tidak ada, halaman tidak valid
    if not title_element:
        print("Halaman tidak valid — bukan product page")
        return None
    title = title_element.text.strip()
    
    asin_element = soup.select_one('#ASIN')
    asin = asin_element.get('value') if asin_element else None
    
    category_element = soup.select_one('#wayfinding-breadcrumbs_feature_div')
    category = category_element.text.strip() if category_element else None
    
    image_url_element = soup.select_one('#landingImage')
    image_url = image_url_element.get('src') if image_url_element else None
    
    check_stock_element = soup.select_one('#outOfStock')
    is_in_stock = True
    price = 0
    original_price = 0
    is_prime = ''
    
    if check_stock_element:
    
        is_in_stock = False
        
    else:
        price_element = soup.select_one('.apex-pricetopay-value span[aria-hidden="true"]')
        price = price_element.text.strip() if price_element else 0
        price = clean_price(price)
        
        original_price_element = soup.select_one('.a-text-price.apex-basisprice-value .a-offscreen')
        if original_price_element:
            original_price = original_price_element.text if original_price_element else 0
            original_price = clean_price(original_price)
        else: 
            original_price = price
        
    is_prime_element = soup.select_one('#usePrimeHandler')
    is_prime = is_prime_element.get('value') if is_prime_element else None
    is_prime = parse_bool(is_prime)
    
    brand_element = soup.select_one('#bylineInfo .a-link-normal')
    
    if brand_element:
        brand = brand_element.text if brand_element else None
    else:
        brand_element = soup.select_one('#bylineInfo')
        brand = brand_element.text if brand_element else None

    brand = extract_brand(brand)
    
    rating_element = soup.select_one('#acrPopover')
    rating = rating_element.get('title') if rating_element else 0
    print(f'Rating: {rating}')
    rating = clean_rating(rating)
    
    review_count_element = soup.select_one('#acrCustomerReviewText span[aria-hidden="true"]')
    review_count = review_count_element.text if review_count_element else 0
    review_count = clean_review_count(review_count)
    
    res = {
        "ASIN": asin,
        "title": title,
        "brand": brand,
        "category": category,
        "image_url": image_url,
        "price": price,
        "original_price": original_price,
        "is_in_stock": is_in_stock,
        "is_prime": is_prime,
        "rating": rating,
        "review_count": review_count
    }
    
    return res
    
# res = fetch_html('https://www.amazon.com/dp/B0FG28SG1N/ref=sspa_dk_detail_right_aax_0?psc=1&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfcmlnaHRfc2hhcmVk')

# res = fetch_html('https://www.amazon.com/dp/B0FXHB7P7X/')

# res = fetch_html('https://www.amazon.com/gp/aw/d/B0CJ22C9MB/')

# res = fetch_html('https://www.amazon.com/dp/B0CQ4HYRM7/ref=sspa_dk_detail_0?pd_rd_i=B0CQ4HYRM7&pd_rd_w=gRIyF&content-id=amzn1.sym.85ceacba-39b1-4243-8f28-2e014f9512c7&pf_rd_p=85ceacba-39b1-4243-8f28-2e014f9512c7&pf_rd_r=FF5FPQCXCH2DYN5Y19F0&pd_rd_wg=StZmU&pd_rd_r=1e75c12b-4ba2-4f59-a501-7defb088b96a&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfdGhlbWF0aWM&th=1')

# process_html(res)