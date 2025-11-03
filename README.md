
# Datenerfassung


## Kurzbeschreibung

Dieses Projekt stellt eine einfache Web-Anwendung zur Datenerfassung bereit. Die Projektstruktur enthält eine `main.py` und ein `install.py`-Skript zur Ersteinrichtung. Statische Dateien und Templates befinden sich in den Verzeichnissen `static/` und `templates/`.

## Voraussetzungen

- Python 3.7+
- Git (optional)

## Schnelle Installation (empfohlen)

1. Repository klonen (falls noch nicht lokal):

```bash
git clone https://github.com/JonGae007/Ehemaligen-Datenerfassung
cd Datenerfassung
```

2. Abhängigkeiten installieren

Das Projekt enthält kein festes `requirements.txt` in der Repo-Wurzel (falls doch vorhanden: `pip install -r requirements.txt`). Alternativ kann `install.py` Hilfestellung leisten:

```bash
python3 install.py
```

Wenn `install.py` nicht alle Abhängigkeiten installiert, verwende:

```bash
# Beispiel (anpassen, falls Flask verwendet wird)
pip install flask
```

3. Anwendung starten

Falls `main.py` nicht automatishc durch `install.py` gestartet wirk kann es so gestartet werden:

```bash
python3 main.py
```

Öffne dann im Browser `http://127.0.0.1` bzw. die URL/IP.

## Projektstruktur

- `main.py` — Einstiegspunkt der Anwendung.
- `install.py` — Setup-/Installationsskript
- `static/` — statische Dateien (JS/CSS).
- `templates/` — HTML-Templates.

Konkrete Dateien im Repository:

- `templates/index.html` — Startseite
- `templates/admin_login.html` — Admin-Login
- `templates/admin_dashboard.html` — Admin-Dashboard
- `templates/admin_benutzer.html` — Benutzerverwaltung
- `templates/admin_jahrgaenge.html` — Jahrgänge
- `templates/datenschutz.html` — Datenschutzerklärung
- `static/script.js` — Client-Script
- `static/style.css` — Stylesheet



## Troubleshooting

- Fehler: "ModuleNotFoundError" — Stelle sicher, dass die virtuelle Umgebung aktiv ist und alle Abhängigkeiten installiert sind.
- Port bereits belegt — wähle einen anderen Port oder beende den Prozess, der den Port nutzt (z. B. `lsof -i :5000`).
- Templates oder statische Dateien werden nicht geladen — überprüfe den Pfad und ob `main.py` die richtigen `template_folder` / `static_folder` übergibt.



## Kontakt

Bei Fragen oder Problemen erstelle bitte ein Issue oder kontaktiere den Ersteller.