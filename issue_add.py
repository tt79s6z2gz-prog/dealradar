"""Übernimmt vorausgefüllte DealRadar-Produktanfragen sicher in den Katalog.

Dieses Skript wird ausschließlich auf owner-authentifizierten GitHub Issues aufgerufen.
GitHub Issue-Texte werden als Daten behandelt, nicht als Code.
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "produkte.json"
DATA = ROOT / "docs" / "data" / "prices.json"

def slugify(value):
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(x for x in value if not unicodedata.combining(x))
    return re.sub(r"(^-+|-+$)", "", re.sub(r"[^a-z0-9]+", "-", value))[:65] or "produkt"

def parse_request(event):
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    issue = event.get("issue", {})
    actor = issue.get("user", {}).get("login", "")
    if not owner or actor.lower() != owner.lower():
        raise ValueError("Nur der Repository-Eigentümer darf Produkte hinzufügen.")
    if not str(issue.get("title", "")).startswith("[DealRadar] "):
        raise ValueError("Keine DealRadar-Anfrage.")
    body = issue.get("body", "")
    if not isinstance(body, str) or len(body) > 6000 or not body.startswith("DEALRADAR_PRODUCT_V1\n"):
        raise ValueError("Ungültiges Anfrageformat.")
    item = json.loads(body.split("\n", 1)[1])
    if not isinstance(item, dict) or set(item) != {"name", "category", "shop", "url"}:
        raise ValueError("Ungültige Produktfelder.")
    for key, maximum in (("name", 120), ("category", 60), ("shop", 80), ("url", 1200)):
        s = item[key]
        if not isinstance(s, str) or not s.strip() or len(s) > maximum:
            raise ValueError(f"Feld {key} ist ungültig.")
        item[key] = s.strip()
    url = urlsplit(item["url"])
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("Nur HTTPS-Produktlinks zulässig.")
    if url.port not in (None, 443):
        raise ValueError("Unzulässiger Port.")
    if any(x in url.hostname.lower() for x in ("localhost", ".local", ".internal")):
        raise ValueError("Keine lokalen Adressen.")
    return item

def run():
    path = Path(os.environ["GITHUB_EVENT_PATH"])
    item = parse_request(json.loads(path.read_text(encoding="utf-8")))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(catalog, list) or len(catalog) >= 200:
        raise ValueError("Katalog voll oder ungültig.")
    for old in catalog:
        if any(offer.get("url") == item["url"] for offer in old.get("offers", [])):
            print("Dieser Link ist bereits gespeichert.")
            return
    candidate = slugify(item["name"])
    ids = {x.get("id") for x in catalog}
    suffix = 2
    while candidate in ids:
        candidate = slugify(item["name"])[:60] + "-" + str(suffix)
        suffix += 1
    product = {"id": candidate, "name": item["name"], "category": item["category"],
               "offers": [{"shop": item["shop"], "url": item["url"]}]}
    catalog.append(product)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Neues Produkt ohne erfundenen Preis sofort in der App anzeigen.
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data.setdefault("products", [])
    if not any(p.get("id") == candidate for p in data["products"]):
        data["products"].append({
            "id": candidate, "name": item["name"], "category": item["category"],
            "best_price_cents": None, "best_shop": None, "best_url": item["url"],
            "last_success_at": None, "fresh": False, "offers": [], "errors": []
        })
    data.setdefault("history", {})[candidate] = []
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Produkt hinzugefügt:", candidate)

if __name__ == "__main__":
    run()
