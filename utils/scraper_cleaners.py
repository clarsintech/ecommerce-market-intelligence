import re

def clean_price(price_str):
    
    if not price_str:
        return 0.0

    price_str = price_str.strip()

    # ambil hanya angka, titik, koma
    price_str = re.sub(r"[^\d.,]", "", price_str)

    # CASE 1: ada koma & titik
    if "," in price_str and "." in price_str:
        # kalau koma di belakang → itu decimal (EU)
        if price_str.rfind(",") > price_str.rfind("."):
            price_str = price_str.replace(".", "").replace(",", ".")
        else:
            price_str = price_str.replace(",", "")

    # CASE 2: hanya koma
    elif "," in price_str:
        price_str = price_str.replace(",", ".")

    # CASE 3: hanya titik → biarkan

    return float(price_str)

def clean_rating(rating):
    if not rating:
        return 0

    match = re.search(r"[\d.,]+", rating)
    if match:
        value = match.group().replace(",", ".")
        return float(value)

    return 0

def clean_review_count(text):
    if not text:
        return 0
    
    match = re.search(r"\d[\d,]*", text)
    if match:
        number = match.group().replace(",", "")
        return int(number)

    return 0
    
def extract_brand(text: str) -> str:
    if not text:
        return None

    match = re.search(r"Visit the (.*?) Store", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        return text.split(":", 1)[-1].strip()


def parse_bool(value):
    if value is None:
        return False

    # handle integer
    if isinstance(value, int):
        return value == 1

    # handle string
    if isinstance(value, str):
        value = value.strip().lower()

        return value in ["1", "in stock", "true"]

    return False