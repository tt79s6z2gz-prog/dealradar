"""Öffentliche HTTPS-Seiten, robots.txt und keine Weiterleitungen."""
import ipaddress
import socket
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import httpx
from parsing import extract_eur_price

USER_AGENT = "DealRadarPrivatePriceMonitor/1.0 (noncommercial; robots-compliant)"

def validate_public_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Nur öffentliche HTTPS-Adressen erlaubt.")
    if parsed.port not in (None, 443): raise ValueError("Nichtstandard-Ports verboten.")
    if len(url) > 2048: raise ValueError("Link zu lang.")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".local", ".internal", ".test", ".localhost")):
        raise ValueError("Lokale Adressen verboten.")
    try:
        ips = [entry[4][0] for entry in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]
    except (socket.gaierror, OSError) as exc:
        raise ValueError("Hostname nicht auflösbar.") from exc
    if not ips or not all(ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError("Nur öffentliche Internetadressen erlaubt.")
    return host

def fetch_price(url: str, selector: str | None = None) -> int:
    host = validate_public_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9",
               "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(headers=headers, timeout=12.0, follow_redirects=False, trust_env=False) as client:
        robots = client.get(f"https://{host}/robots.txt")
        if robots.status_code == 404:
            pass
        elif robots.status_code == 200:
            parser = RobotFileParser()
            parser.parse(robots.text.splitlines())
            if not parser.can_fetch(USER_AGENT, url):
                raise ValueError("robots.txt verbietet den Abruf.")
        else:
            raise ValueError(f"robots.txt unklar ({robots.status_code}).")
        response = client.get(url)
        if response.is_redirect: raise ValueError("Weiterleitung; endgültige Produkt-URL erforderlich.")
        if response.status_code in (401, 403, 429): raise ValueError("Automatisierter Abruf blockiert.")
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""): raise ValueError("Kein HTML.")
        if len(response.content) > 3_000_000: raise ValueError("Produktseite zu groß.")
        value = extract_eur_price(response.text, selector)
        if not value: raise ValueError("Kein eindeutiger EUR-Produktpreis gefunden.")
        return value
