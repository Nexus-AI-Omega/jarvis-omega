# Jarvis – Grundgerüst

Ein persönlicher KI-Assistent für zu Hause, den man mit **„Hey Jarvis“** anspricht –
mit Stimme, einem Gesicht im LED-Look, Telegram und Home Assistant.

Entstanden aus einem privaten Projekt, das über Monate gewachsen ist. Dieses Grundgerüst
enthält den aufgeräumten Kern; alles Persönliche ist entfernt, der Rest ist zum Selbstausbauen da.

## Was Jarvis kann

| Bereich | Beispiele |
|---|---|
| **Zuhören** | Weckwort „Hey Jarvis“, danach einfach sprechen. Nach einer Antwort kann man ein paar Sekunden ohne Weckwort nachfragen. Die Spracherkennung läuft auf dem eigenen Rechner. |
| **Sprechen** | Natürliche Stimme über ElevenLabs. Der Mund im Gesicht bewegt sich mit. |
| **Gesicht** | Ein Fenster mit einem LED-Gesicht: blau in Ruhe, gelb beim Nachdenken. Optional zusätzlich auf einer echten LED-Matrix (WLED, 16×16 oder 64×64). |
| **Alltag** | „Wie wird das Wetter morgen?“ · „Stell einen Timer auf zehn Minuten für die Nudeln“ · „Erinnere mich morgen um acht an den Müll“ |
| **Gedächtnis** | „Merk dir, dass meine Schwester Anna heißt“ – Jarvis weiß es auch nach einem Neustart. |
| **Zuhause** | Mit Home Assistant: „Mach das Licht im Wohnzimmer aus“ · „Wie warm ist es im Bad?“ Kühlschrank, Waschmaschine & Co. stehen auf einer Schutzliste und werden nie geschaltet. |
| **Kalender & Mail** | Optional: „Was steht morgen an?“ · „Habe ich neue Mails?“ (nur lesen) |
| **Telegram** | Jarvis per Chat schreiben oder Sprachnachrichten schicken – auch unterwegs. Timer und Erinnerungen kommen dort ebenfalls an. |
| **Ruhe** | Nachtruhe (z. B. 23–7 Uhr) und ein Ruhemodus („Ruhemodus an“): Jarvis meldet sich nicht von selbst, das Gesicht ist dunkel. |

## Was man braucht

- Einen Rechner mit **Linux** (getestet mit Ubuntu). macOS und Windows sollten mit kleinen
  Anpassungen gehen, sind aber nicht getestet.
- Ein **Mikrofon** und **Lautsprecher**.
- **Claude Pro** (rund 21 € im Monat) – zwingend, denn Einrichtung und Ausbau laufen über Claude Code.
- **Claude-Guthaben** für Jarvis' „Gehirn“ (console.anthropic.com) – getrennt vom Abo, nach
  Verbrauch; mit dem voreingestellten Modell Claude Haiku kostet ein normaler Tag meist nur wenige Cent.
- **ElevenLabs** (elevenlabs.io) für die Stimme – rund 7 € im Monat.
- Optional: Telegram, Home Assistant, einen Kalender (iCal-Adresse), ein E-Mail-Postfach,
  eine WLED-Matrix und einen Gemini-Zugang als Ersatz, falls Claude einmal nicht erreichbar ist.

## Einrichten

Am einfachsten mit **Claude Code**: Ordner öffnen und schreiben „**Richte Jarvis ein**“.
Claude prüft dann die Voraussetzungen, installiert alles, fragt nach Name, Anrede und
Zugängen und testet zum Schluss. Was dabei passiert, steht in [SETUP.md](SETUP.md).

Von Hand (Linux):

```bash
sudo apt install python3-venv ffmpeg libportaudio2
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps openwakeword==0.6.0
cp config.example.json config.json      # danach config.json ausfüllen
.venv/bin/python jarvis.py --text       # erst einmal im Textmodus ausprobieren
bash scripts/starten.sh                 # richtig starten, mit Fenster
bash scripts/autostart-einrichten.sh    # optional: bei jeder Anmeldung starten
```

## Aufbau

| Datei | Aufgabe |
|---|---|
| `jarvis.py` | Startet alles, Fenster-Server, verbindet Zuhören, Gehirn und Stimme |
| `ohr.py` | Mikrofon, Weckwort, Aufnahme, Spracherkennung |
| `gehirn.py` | Claude mit Werkzeugen, Persönlichkeit, Gemini als Ersatz |
| `stimme.py` | ElevenLabs-Stimme, Wiedergabe, Mundbewegung |
| `gesicht.py` | Das LED-Gesicht (und die optionale WLED-Matrix) |
| `gedaechtnis.py`, `termine.py`, `wetter.py`, `hausautomation.py`, `kalender.py`, `post.py` | Die Werkzeuge |
| `telegram_bot.py` | Telegram |
| `ruhe.py` | Nachtruhe und Ruhemodus |
| `frontend/` | Das Fenster mit dem Gesicht |
| `daten/` | Was Jarvis sich merkt (wird nie mitgegeben) |

Ein neues Werkzeug einbauen: eine Funktion schreiben, sie in `gehirn.py` bei `_werkzeuge()`
beschreiben und in `_ausfuehren()` aufrufen – fertig. Claude Code hilft dabei gern.

## Lizenz

MIT – siehe [LICENSE](LICENSE). Nutzen, verändern und weitergeben ausdrücklich erlaubt,
ohne Gewähr.
