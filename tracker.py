"""DealRadar: öffentlicher Preis-Monitor über GitHub Actions."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from fetcher import fetch_price

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "produkte.json"
OUTPUT = ROOT / "docs" / "data" / "prices.json"
ALERT_PERCENT = 10
ALERT_CENTS = 300
MAX_HISTORY = 180
MAX_ALERTS = 80

def valid_catalog(items):
    if not isinstance(items, list) or len(items) > 200:
        raise ValueError("produkte.json muss ein Array mit höchstens 200 Produkten sein.")
    used = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Produkt muss ein Objekt sein.")
        key, name = item.get("id"), item.get("name")
        if not isinstance(key, str) or not key or len(key) > 80 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in key):
            raise ValueError("Ungültige Produkt-ID.")
        if key in used: raise ValueError("Doppelte Produkt-ID.")
        used.add(key)
        if not isinstance(name, str) or not (2 <= len(name) <= 120): raise ValueError("Ungültiger Produktname.")
        offers = item.get("offers")
        if not isinstance(offers, list) or not (1 <= len(offers) <= 8): raise ValueError("1 bis 8 Angebote pro Produkt erforderlich.")
        urls = set()
        for offer in offers:
            if not isinstance(offer, dict) or not isinstance(offer.get("shop"), str) or not offer["shop"]:
                raise ValueError("Shopname fehlt.")
            url = offer.get("url", "")
            if not isinstance(url, str) or len(url) > 2048 or urlsplit(url).scheme != "https" or not urlsplit(url).hostname:
                raise ValueError("Öffentlicher HTTPS-Produktlink erforderlich.")
            if url in urls: raise ValueError("Doppelte Shop-URL.")
            urls.add(url)
            selector = offer.get("selector")
            if selector is not None and (not isinstance(selector, str) or len(selector) > 160):
                raise ValueError("Ungültiger CSS-Selektor.")
    return items

def read_json(path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError: return fallback

def telegram_alert(alerts):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not (alerts and token and chat): return False
    text = "DealRadar Preisalarm\n\n" + "\n\n".join(
        f"📉 {a['name']}: {a['previous_price_cents']/100:.2f} € → {a['price_cents']/100:.2f} € (−{a['drop_pct']:.1f} %)\n{a['url']}"
        for a in alerts[:10])
    body = json.dumps({"chat_id": chat, "text": text, "disable_web_page_preview": True}).encode("utf-8")
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body,
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=12) as response:
        if response.status != 200: raise RuntimeError("Telegram-Versand fehlgeschlagen.")
    return True

def scan(fetch=fetch_price, send=telegram_alert, now=None):
    catalog = valid_catalog(read_json(CONFIG, []))
    previous = read_json(OUTPUT, {})
    past = previous.get("history", {}) if isinstance(previous.get("history"), dict) else {}
    old_latest = {p["id"]: p for p in previous.get("products", []) if isinstance(p, dict) and "id" in p}
    at = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    products, history, alerts = [], {}, []
    successes = errors = 0
    for item in catalog:
        pid = item["id"]
        measured, failed = [], []
        for offer in item["offers"]:
            try:
                price = fetch(offer["url"], offer.get("selector"))
                if not isinstance(price, int) or isinstance(price, bool) or not 0 < price <= 1000000000:
                    raise ValueError("Ungültiger Preis.")
                measured.append({"shop": offer["shop"], "price_cents": price, "url": offer["url"]})
                successes += 1
            except Exception as exc:
                errors += 1
                failed.append(f"{offer['shop']}: {str(exc)[:140]}")
        best = min(measured, key=lambda x: x["price_cents"]) if measured else None
        samples = list(past.get(pid, [])) if isinstance(past.get(pid, []), list) else []
        prior = old_latest.get(pid, {}).get("best_price_cents")
        if best:
            samples.append({"time": at, "price_cents": best["price_cents"]})
            samples = samples[-MAX_HISTORY:]
            if isinstance(prior, int) and prior > best["price_cents"]:
                drop = prior - best["price_cents"]
                pct = round(drop * 100 / prior, 1)
                if drop >= ALERT_CENTS and pct >= ALERT_PERCENT:
                    alerts.append({"id": f"{pid}-{at}", "product_id": pid, "name": item["name"],
                                   "at": at, "previous_price_cents": prior,
                                   "price_cents": best["price_cents"], "drop_pct": pct, "url": best["url"]})
        history[pid] = samples[-MAX_HISTORY:]
        old = old_latest.get(pid, {})
        products.append({"id": pid, "name": item["name"], "category": item.get("category", "Sonstiges"),
                         "best_price_cents": best["price_cents"] if best else old.get("best_price_cents"),
                         "best_shop": best["shop"] if best else old.get("best_shop"),
                         "best_url": best["url"] if best else old.get("best_url"),
                         "last_success_at": at if best else old.get("last_success_at"),
                         "fresh": bool(best), "offers": measured, "errors": failed})
    prior_alerts = previous.get("alerts", [])
    if not isinstance(prior_alerts, list): prior_alerts = []
    data = {"generated_at": at, "products": products, "history": history,
            "alerts": (alerts + prior_alerts)[:MAX_ALERTS],
            "summary": {"checked": sum(len(x["offers"]) for x in catalog),
                        "successful": successes, "failed": errors},
            "notice": "Nur Preise aus erfolgreich auslesbaren Produktlinks; keine Versandkosten oder Marktpreisgarantie."}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try: send(alerts)
    except Exception as exc: print("Telegram-Warnung:", str(exc)[:160])
    print(f"Prüfung: {len(products)} Produkte / {successes} Angebote / {errors} Fehler / {len(alerts)} Alarme")
    return data

if __name__ == "__main__": scan()
