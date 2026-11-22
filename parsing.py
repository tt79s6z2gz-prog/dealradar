"""Liest ausdrücklich ausgezeichnete EUR-Produktpreise aus strukturiertem HTML."""
import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from bs4 import BeautifulSoup

def price_cents(value):
    if value is None or isinstance(value, bool): return None
    s = str(value).replace("\xa0", " ").replace("\u202f", " ")
    match = re.search(r"\d[\d\s.,]*", s)
    if not match: return None
    digits = re.sub(r"\s+", "", match.group()).rstrip(",.")
    if not digits: return None
    if "," in digits and "." in digits:
        decimal = "," if digits.rfind(",") > digits.rfind(".") else "."
        digits = digits.replace("." if decimal == "," else ",", "").replace(decimal, ".")
    elif "," in digits or "." in digits:
        sep = "," if "," in digits else "."
        parts = digits.split(sep)
        if len(parts) > 2:
            digits = "".join(parts[:-1]) + ("." + parts[-1] if len(parts[-1]) <= 2 else parts[-1])
        elif len(parts[-1]) == 3: digits = "".join(parts)
        else: digits = digits.replace(sep, ".")
    try:
        result = int((Decimal(digits) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return result if result > 0 else None
    except (InvalidOperation, ValueError): return None

def walk(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values(): yield from walk(nested)
    elif isinstance(value, list):
        for nested in value: yield from walk(nested)

def typed(value, typename):
    types = value.get("@type", [])
    if isinstance(types, str): types = [types]
    return any(isinstance(t, str) and (t == typename or t.endswith("/" + typename)) for t in types)

def offer_prices(offers):
    if isinstance(offers, list):
        for offer in offers: yield from offer_prices(offer)
    elif isinstance(offers, dict):
        currency = offers.get("priceCurrency")
        if currency and str(currency).upper() != "EUR": return
        key = "lowPrice" if typed(offers, "AggregateOffer") else "price"
        val = price_cents(offers.get(key))
        if val: yield val
        if key == "price":
            for spec in walk(offers.get("priceSpecification")):
                if not spec.get("priceCurrency") or str(spec["priceCurrency"]).upper() == "EUR":
                    val = price_cents(spec.get("price"))
                    if val: yield val

def extract_eur_price(html: str, selector: str | None = None) -> int | None:
    soup = BeautifulSoup(html, "html.parser")
    if selector:
        try: element = soup.select_one(selector)
        except Exception as exc: raise ValueError("Ungültiger CSS-Selektor.") from exc
        if element is None: return None
        for value in (element.get("content"), element.get("data-price"), element.get_text(" ", strip=True)):
            val = price_cents(value)
            if val: return val
        return None
    for tag in soup.select('script[type="application/ld+json"]'):
        try: data = json.loads(tag.string or tag.get_text())
        except (TypeError, json.JSONDecodeError): continue
        for obj in walk(data):
            if typed(obj, "Product"):
                prices = list(offer_prices(obj.get("offers")))
                if prices: return min(prices)
    for css in ('meta[property="product:price:amount"]', 'meta[property="og:price:amount"]',
                'meta[itemprop="price"]', '[itemprop="price"][content]'):
        element = soup.select_one(css)
        if element:
            val = price_cents(element.get("content"))
            if val: return val
    return None
