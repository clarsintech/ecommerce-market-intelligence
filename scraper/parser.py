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
    # print(f'Rating: {rating}')
    rating = clean_rating(rating)
    
    review_count_element = soup.select_one('#acrCustomerReviewText')
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
    
def process_search_results(response, max_results):
    if response:
        soup = BeautifulSoup(response, 'lxml')
    else:
        print('gada produk')
        return
    
    # if "Something went wrong" in soup or "sorry" in soup.lower():
    #     print("Amazon error page detected")
    #     return []
    
    # Mencari div yang merupakan hasil pencarian produk
    items = soup.find_all('div', {'role': 'listitem'})

    results = []
    counter = 0
    for item in items:
        data = {}
        # 1. Title Recipe (Div pembungkus judul & toko) -> cek dulu dia produk sponsored atau engga
        title_recipe = item.find('div', attrs={'data-cy': 'title-recipe'})
        price_node = item.find('span', class_='a-price')
        if not price_node:
            continue
        if title_recipe:
            # Seller Name (H2 class a-size-mini)
            # seller_node = title_recipe.find('div')
            # data['seller_name'] = seller_node.get_text(strip=True) if seller_node else None
            
            # ini skip dulu, lgsg masuk ke product name aja dulu

            # Product Name (H2 class a-size-base-plus)
            # name_node = title_recipe.find('span')
            if 'Sponsored' in title_recipe.getText(strip=True):
                continue
            data['title'] = title_recipe.get_text(strip=True) if title_recipe else None
            counter+=1
        
        
        # Lewati jika ASIN kosong (biasanya iklan atau spacer)
        asin = item.get('data-asin')
        if not asin:
            continue

        data['ASIN'] = asin

        # print(item)
        # 2. Product Image (src dari class s-image)
        img = item.find('img', class_='s-image')
        data['image_url'] = img.get('src') if img else None


        # 3. Reviews & Ratings
        review_slot = item.find('i', attrs={'data-cy': 'reviews-ratings-slot'})
        data['rating'] = 0
        if review_slot:
            # Rating (4.5 out of 5 stars)
            data['rating'] = clean_rating(review_slot.get_text(strip=True)) if review_slot else 0

        review_node = item.find('div', attrs={'data-csa-c-slot-id': 'alf-reviews'})
        data['review_count'] = 0
        if review_node:
            link = review_node.find('a')
            if link:
                review_text = link.get('aria-label')
                # Review => '4,336 ratings'
                data['review_count'] = clean_review_count(review_text)

        # 4. Prices
        # Harga Sekarang (a-offscreen)
        data['price']=0
        price_node = item.find('span', class_='a-price')
        if price_node:
            offscreen = price_node.find('span', class_='a-offscreen')
            data['price'] = clean_price(offscreen.get_text(strip=True)) if offscreen else None

        original_price_span = item.find('span', class_='a-text-price', attrs={'data-a-size': 'b', 'data-a-strike': 'true'})
        data['original_price'] = 0
        if original_price_span:
            hidden_span = original_price_span.find('span', attrs={'aria-hidden': 'true'})
            if hidden_span:
                data['original_price'] = clean_price(hidden_span.get_text(strip=True))
            else:
                data['original_price'] = 0
        else:
            data['original_price'] = 0
        
        data['is_prime'] = False
        
        # Prime products
        prime_node = item.find('div', attrs={'data_cy': 'price_recipe'})
        if prime_node:
            if "Exclusive Prime price" in prime_node.get_text():
                data['is_prime'] = True
                
        results.append(data)
        
        if counter >= max_results:
            break

    # Print hasil untuk cek
    for res in results:
        print(res)
    return results

# process_html(res)