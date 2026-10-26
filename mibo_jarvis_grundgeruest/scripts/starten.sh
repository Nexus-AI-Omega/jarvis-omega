#!/usr/bin/env bash
# Jarvis starten (Linux): Programm im Hintergrund, danach das Fenster mit dem Gesicht.
# Laeuft Jarvis schon, wird nur das Fenster geoeffnet.

ORDNER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ORDNER" || exit 1
PORT=$(python3 -c "import json; print(json.load(open('config.json')).get('port', 8340))" 2>/dev/null || echo 8340)

if ! curl -s -o /dev/null "http://localhost:$PORT"; then
    PY=python3
    [ -x .venv/bin/python ] && PY=.venv/bin/python
    nohup "$PY" jarvis.py >> daten/jarvis.log 2>&1 &
    for _ in $(seq 60); do
        curl -s -o /dev/null "http://localhost:$PORT" && break
        sleep 1
    done
fi

# Eigenes Fenster ohne Adressleiste, wenn Chrome/Chromium da ist — sonst der Standard-Browser
for b in google-chrome chromium chromium-browser; do
    if command -v "$b" > /dev/null; then
        exec "$b" --app="http://localhost:$PORT" --start-fullscreen > /dev/null 2>&1
    fi
done
xdg-open "http://localhost:$PORT"
