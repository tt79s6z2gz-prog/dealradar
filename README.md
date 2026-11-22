# DealRadar – deine Schnäppchen-Web-App

Für **iPhone 16 und iPad**, ohne Mac. Alle Produktkategorien, auch Kinderspielzeug.

## Status und wichtige Grenzen
Die Web-App zeigt **nur Produkte, deren echte Shop-URLs in `produkte.json` stehen**. Sie durchsucht nicht eigenständig sämtliche Händler und importiert keinen bestehenden idealo-Preisverlauf. Ohne eingetragene URLs sind Preise und Produktlisten zunächst leer. Shop-Sperren und Captchas werden nicht umgangen. Versandkosten sind nicht enthalten.

**Geplante Preisprüfung:** alle 30 Minuten von 06:00 bis einschließlich 23:30 Uhr, täglich (Europe/Berlin): 36 geplante Komplettprüfungen. GitHub Actions kann verspätet starten oder Läufe auslassen.

**Alarmschwelle:** mindestens 10 % **und** 3 € Preissenkung zwischen erfolgreichen Messungen. Die App zeigt Alarme beim Öffnen; echte iOS-Push-Nachrichten sind nicht enthalten. Telegram ist optional (GitHub Actions Secrets).

## Produkt einfacher aus der App hinzufügen (neu)

1. In DealRadar **„＋ Produkt beobachten“** antippen und einen Produktlink (idealo, Geizhals oder Shop) einfügen.
2. **„Produkt vormerken →“** antippen. GitHub öffnet eine bereits ausgefüllte Anfrage.
3. Dort einmal **„Submit new issue“** bestätigen. Der Workflow `produkt-hinzufuegen.yml` aktualisiert `produkte.json` und die App-Produktliste automatisch.
4. Nach dem neuen Eintrag startet im selben Workflow eine **sofortige Komplettprüfung aller Produkte und Shop-Angebote**, auch nachts. Sobald die GitHub-Aktion fertig ist, lädt die App beim Öffnen oder im geöffneten Zustand spätestens beim nächsten minütlichen Abruf die neuen Ergebnisse. Ein Preis erscheint nur bei erfolgreicher Messung.

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
2. Neue Produkte aus der App starten automatisch eine Komplettprüfung. Für einen manuellen Prüflauf **Actions → DealRadar Preise alle 30 Minuten prüfen → Run workflow** öffnen.
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

## Aktualisierungslogik

- Die **Preisprüfung auf GitHub** wird zwischen 06:00 und 23:30 Uhr alle 30 Minuten angestoßen. Nach 23:30 Uhr folgt der nächste reguläre Lauf um 06:00 Uhr.
- **Bei jeder Produktaufnahme über die App** führt derselbe GitHub-Actions-Job nach dem Speichern sofort den Preisprüfer über den **gesamten Katalog** aus; ein neuer GitHub-Token-Push muss deshalb keine weitere Aktion auslösen.
- Bei Änderungen an `produkte.json` durch normale Repository-Pushes löst auch ein `push`-Ereignis die vollständige Preisprüfung aus. Pushes innerhalb von GitHub Actions mit `GITHUB_TOKEN` lösen diesen zweiten Workflow nicht erneut aus; dies wird durch den direkten Komplettlauf im Aufnahme-Workflow abgefangen.
- Die iPhone/iPad-Web-App lädt Ergebnisse beim Öffnen/Zurückkehren und während der Nutzung minütlich nach. Sie verwendet die jeweils veröffentlichten Messwerte; **ein Nachladen ist keine neue Shop-Abfrage**.
- **Einschränkungen:** GitHub-Actions-Start und Seitenveröffentlichung dauern möglicherweise einige Minuten. Shop-Sperren verhindern ggf. erfolgreiche Preisabfragen. Ein iOS-Pushdienst ist noch nicht eingebaut.
