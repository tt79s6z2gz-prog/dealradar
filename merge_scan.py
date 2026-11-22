"""Merge scanned prices with the newest GitHub catalog after a concurrent edit.

A scan can finish after the owner has added more products. Do not replace
newer data or remove those products when retrying a rejected Git push.
"""
import json
import sys
from pathlib import Path

def merge(scan, latest, catalog):
    scan_products = {p["id"]: p for p in scan.get("products", []) if isinstance(p, dict) and p.get("id")}
    latest_products = {p["id"]: p for p in latest.get("products", []) if isinstance(p, dict) and p.get("id")}
    scan_history = scan.get("history") or {}
    latest_history = latest.get("history") or {}
    result = {**latest, "products": [], "history": {}}
    for item in catalog:
        key = item["id"]
        current = latest_products.get(key, {})
        pending = scan_products.get(key, {})
        newer_measurement = (
            current.get("last_success_at")
            and pending.get("last_success_at")
            and current["last_success_at"] > pending["last_success_at"]
        )
        chosen = current if newer_measurement else (pending or current)
        price_record = chosen if chosen.get("best_price_cents") is not None else current
        record = {
            "id": key,
            "name": item.get("name", key),
            "category": item.get("category", "Sonstiges"),
            "best_price_cents": price_record.get("best_price_cents"),
            "best_shop": price_record.get("best_shop"),
            "best_url": price_record.get("best_url") or item["offers"][0]["url"],
            "last_success_at": price_record.get("last_success_at"),
            "fresh": bool(chosen.get("fresh", False)),
            "offers": chosen.get("offers", []),
            "errors": chosen.get("errors", []),
        }
        result["products"].append(record)
        samples = {}
        for entry in (latest_history.get(key, []) + scan_history.get(key, [])):
            if isinstance(entry, dict) and isinstance(entry.get("time"), str) and isinstance(entry.get("price_cents"), int):
                samples[(entry["time"], entry["price_cents"])] = entry
        result["history"][key] = [samples[k] for k in sorted(samples)[-180:]]
    alerts = {}
    for entry in (latest.get("alerts", []) + scan.get("alerts", [])):
        if isinstance(entry, dict) and entry.get("id"):
            alerts[entry["id"]] = entry
    result["alerts"] = sorted(alerts.values(), key=lambda a: a.get("at", ""), reverse=True)[:80]
    times = [t for t in [latest.get("generated_at"), scan.get("generated_at")] if isinstance(t, str)]
    result["generated_at"] = max(times) if times else None
    if not latest.get("generated_at") or (scan.get("generated_at") and scan["generated_at"] >= latest["generated_at"]):
        result["summary"] = scan.get("summary", {})
    result["notice"] = scan.get("notice") or latest.get("notice", "")
    return result

def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python merge_scan.py SCAN_JSON LATEST_JSON CATALOG_JSON")
    scan_path, latest_path, catalog_path = map(Path, sys.argv[1:])
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    result = merge(scan, latest, catalog)
    latest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Merged {len(result['products'])} products, {len(result['alerts'])} alarms, generated_at={result['generated_at']}")

if __name__ == "__main__":
    main()
