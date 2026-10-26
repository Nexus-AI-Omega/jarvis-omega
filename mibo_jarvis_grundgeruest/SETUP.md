# Einrichtung (Anleitung für Claude Code)

Diese Datei richtet sich an Claude Code. Sagt jemand „Richte Jarvis ein“, arbeite sie
Schritt für Schritt ab. Sprich die Person in einfachen Worten an, erkläre Fachbegriffe kurz
und frage immer nur nach einer Sache auf einmal.

## 1. Voraussetzungen prüfen und installieren

1. Betriebssystem feststellen. Getestet ist Linux (Ubuntu/Debian). Bei macOS oder Windows
   ehrlich sagen, dass es nicht getestet ist, und die Befehle sinngemäß anpassen
   (macOS: `brew install python ffmpeg portaudio`; Windows: `winget install Python.Python.3.12`
   und `winget install Gyan.FFmpeg`).
2. Python 3.10 oder neuer (`python3 --version`).
3. Linux-Pakete: `sudo apt install python3-venv ffmpeg libportaudio2` (braucht das Passwort
   der Person – den Befehl zeigen und sie selbst eintippen lassen, falls du kein sudo hast).
4. Virtuelle Umgebung und Pakete:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/pip install --no-deps openwakeword==0.6.0
   ```
   (openWakeWord wird ohne Abhängigkeiten installiert, weil es sonst `tflite-runtime`
   verlangt, das es für neuere Python-Versionen nicht gibt. Jarvis nutzt ONNX.)

## 2. config.json anlegen

`config.example.json` nach `config.json` kopieren. Dann nacheinander fragen und eintragen:

| Frage an die Person | Feld |
|---|---|
| Wie heißt du? | `nutzer_name` |
| Wie soll Jarvis dich ansprechen? (z. B. „Sir“, „Chef“, den Vornamen) | `anrede` |
| Was machst du beruflich? (für den Plauderton, optional) | `taetigkeit` |
| In welcher Stadt wohnst du? (für das Wetter) | `stadt` |
| Claude-Zugang: auf console.anthropic.com → API Keys einen Schlüssel anlegen | `anthropic_api_key` |
| ElevenLabs: auf elevenlabs.io → Profil → API Keys; die Stimme unter „Voices“ aussuchen und ihre Voice-ID kopieren | `elevenlabs_api_key`, `elevenlabs_stimme` |

Danach die Wahlfunktionen anbieten – jede einzeln, alle dürfen übersprungen werden:

- **Telegram:** In Telegram @BotFather öffnen, `/newbot`, Namen vergeben, den Token in
  `telegram_bot_token` eintragen. Jarvis starten, dem neuen Bot `/start` schreiben – er antwortet
  mit der Chat-Nummer; die kommt in `telegram_chat_ids` (Liste), dann Jarvis neu starten.
- **Home Assistant:** Adresse (z. B. `http://homeassistant.local:8123`) in `home_assistant_url`,
  in Home Assistant unter Profil → Sicherheit ein „Langlebiges Zugriffstoken“ anlegen und in
  `home_assistant_token` eintragen. Fragen, welche Geräte nie per Sprache geschaltet werden
  dürfen (außer den eingebauten: Kühlschrank, Gefrierschrank, Waschmaschine, Spülmaschine,
  Trockner, Router, Server) – deren Entitäts-IDs in `schutzliste`.
- **Kalender:** die geheime iCal-Adresse (Google: Kalender-Einstellungen → „Privatadresse im
  iCal-Format“) in `kalender_ics_url`.
- **E-Mail lesen:** `imap_server`, `email_adresse`, `email_passwort` (bei Gmail und iCloud ein
  App-Passwort anlegen, nicht das normale Passwort).
- **LED-Matrix mit WLED:** IP-Adresse in `matrix_ip`. In WLED unter Einstellungen → Sync
  „DDP“ empfangen erlauben (ist meist schon an).
- **Gemini als Ersatz:** Schlüssel von aistudio.google.com in `gemini_api_key`.
- **Nachtruhe:** Zeitraum in `nachtruhe`, Standard `23:00-07:00`.

Mikrofon und Lautsprecher: Normalerweise reichen die Standardgeräte (Felder leer lassen).
Sonst mit `.venv/bin/python -c "import sounddevice; print(sounddevice.query_devices())"`
die Geräte auflisten und den Namen in `mikrofon` bzw. `lautsprecher` eintragen.

## 3. Testen

1. Textmodus: `.venv/bin/python jarvis.py --text` – „Wie wird das Wetter morgen?“ und
   „Stell einen Timer auf eine Minute“ fragen. Klappt das, sind Claude und die Werkzeuge in Ordnung.
2. Richtig starten: `bash scripts/starten.sh`. Das Fenster mit dem Gesicht geht auf.
   Die Person soll „Hey Jarvis, wie spät ist es?“ sagen. Im Protokoll `daten/jarvis.log`
   sieht man `[ohr] Gehoert: …`.
   - Reagiert er nicht auf „Hey Jarvis“: Mikrofon prüfen, ggf. `weckwort_schwelle` auf 0.35 senken.
   - Reagiert er zu oft von allein: Schwelle auf 0.6 erhöhen.
3. Auf Wunsch Autostart: `bash scripts/autostart-einrichten.sh`.

## 4. Zum Schluss

Kurz zusammenfassen, was eingerichtet ist und was nicht, und erwähnen:
- Persönliche Daten liegen nur in `config.json` und `daten/` – beides nie weitergeben.
- Neue Fähigkeiten lassen sich mit Claude Code ergänzen („Bau Jarvis ein Werkzeug für …“).
