# CLAUDE.md

Dieser Ordner ist **Jarvis**, ein persönlicher KI-Assistent mit Weckwort, Stimme,
LED-Gesicht, Telegram und Home Assistant (Python, FastAPI). Überblick: README.md.

## Einrichtung

Sagt die Person „Richte Jarvis ein“ oder fragt nach der Installation, folge **SETUP.md**.

## Beim Weiterbauen

- Neue Werkzeuge: Funktion in einem eigenen Modul, Beschreibung in `gehirn._werkzeuge()`,
  Aufruf in `gehirn._ausfuehren()`. Die Werkzeugliste immer in fester Reihenfolge lassen
  (sonst greift der Zwischenspeicher bei Claude nicht).
- Wechselnde Angaben (Uhrzeit, Zustände) gehören in den Hinweis vor der Frage
  (`gehirn._hinweis`), nicht in den Systemtext.
- Persönliches gehört nur in `config.json` und `daten/` – beides ist von git ausgeschlossen.
- Geräte auf der Schutzliste (`hausautomation.SCHUTZWOERTER`, `schutzliste`) dürfen nie
  geschaltet werden, auch nicht zum Testen.
- Kommentare und Texte auf Deutsch, Code-Stil wie in den vorhandenen Dateien.
