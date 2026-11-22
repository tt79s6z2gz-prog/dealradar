# DealRadar – deine Schnäppchen-Web-App

Für **iPhone 16 und iPad**, ohne Mac. Alle Produktkategorien, auch Kinderspielzeug.

## Status und wichtige Grenzen
Die Web-App zeigt **nur Produkte, deren echte Shop-URLs in `produkte.json` stehen**. Sie durchsucht nicht eigenständig sämtliche Händler und importiert keinen bestehenden idealo-Preisverlauf. Ohne eingetragene URLs sind Preise und Produktlisten zunächst leer. Shop-Sperren und Captchas werden nicht umgangen. Versandkosten sind nicht enthalten.

**Geplante Preisprüfung:** 06:00, 09:00, 12:00, 15:00, 18:00 und 21:00 Uhr in Europe/Berlin (GitHub Actions kann verspätet starten).

**Alarmschwelle:** mindestens 10 % **und** 3 € Preissenkung zwischen erfolgreichen Messungen. Die App zeigt Alarme beim Öffnen; echte iOS-Push-Nachrichten sind nicht enthalten. Telegram ist optional (GitHub Actions Secrets).

## Produkt einfacher aus der App hinzufügen (neu)

1. In DealRadar **„＋ Produkt beobachten“** antippen und einen Produktlink (idealo, Geizhals oder Shop) einfügen.
2. **„Produkt vormerken →“** antippen. GitHub öffnet eine bereits ausgefüllte Anfrage.
3. Dort einmal **„Submit new issue“** bestätigen. Der Workflow `produkt-hinzufuegen.yml` aktualisiert `produkte.json` und die App-Produktliste automatisch.
4. Die DealRadar-App neu laden. Ein Preis erscheint erst nach einer erfolgreichen automatischen Messung.

Für diesen Ablauf musst du bei GitHub angemeldet sein und die Issues-Funktion sowie GitHub Actions müssen aktiviert sein. **Kein JSON-Kopieren nötig.** Die GitHub-Bestätigung ist erforderlich, weil GitHub Pages als statische Website keine vertraulichen Schreibzugangsdaten sicher speichern kann.

**Noch einfacher:** Schick mir den Produktlink hier im Chat, dann kann ich ihn über die verbundene GitHub-Integration hinzufügen.

## Web-App online schalten
1. Repository unter **Settings → Pages** öffnen.
2. Unter **Build and deployment → Source**: **Deploy from a branch**.
3. **Branch main** und Ordner **/docs**, dann **Save** wählen.
4. Die von GitHub angezeigte Adresse im Safari öffnen, normalerweise https://tt79s6z2gz-prog.github.io/dealradar/ .
5. **Teilen → Zum Home-Bildschirm** antippen.

## Preise einschalten
1. Die Datei `produkte.json` bearbeiten. Für jedes Produkt echte Shop-Links angeben. Die Setnummer/Modellvariante muss bei mehreren Shops übereinstimmen.
2. Unter **Actions → Preise prüfen** einen Lauf über **Run workflow** starten.
3. Unter `docs/data/prices.json` nachsehen, ob Preise erfolgreich ausgelesen wurden. Die App lädt diese Datei.
4. Für Telegram-Benachrichtigungen die GitHub-Actions-Secrets `TELEGRAM_BOT_TOKEN` und `TELEGRAM_CHAT_ID` hinterlegen. **Niemals Tokens in Dateien oder Chat-Nachrichten eintragen.**

Beispiel für `produkte.json`:
```json
[
  {
    "id": "lego-beispiel",
    "name": "LEGO Set – genaue Artikelnummer",
    "category": "Kinderspielzeug",
    "offers": [
      {"shop": "Mein Händler", "url": "https://DEINE-ECHTE-PRODUKTSEITE"}
    ]
  }
]
```

**Datenschutz:** Dieses Repository ist öffentlich: Deine eingetragenen Produktlinks und der Preisverlauf sind damit öffentlich sichtbar. Die Merkliste in der App liegt lokal im jeweiligen Gerät.

## Technik
Statische PWA in `docs/`, Preisprüfer in `tracker.py`, GitHub-Workflow unter `.github/workflows/preise.yml`. Der Preisprüfer respektiert robots.txt und unterstützt nur öffentliche HTTPS-Seiten mit auslesbarer Preis-Auszeichnung. Mehrere Händlerangebote werden verglichen; fehlende Daten bleiben als nicht frisch gekennzeichnet.
