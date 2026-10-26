"""Einstellungen aus config.json (Vorlage: config.example.json).

Jeder Wert hat einen Standard, damit Jarvis auch mit einer halb ausgefuellten
Datei startet: Fehlt ein Zugang (z.B. Telegram), ist die Funktion einfach aus.
"""

import json
import os

BASIS = os.path.dirname(os.path.abspath(__file__))
DATEN = os.path.join(BASIS, "daten")
os.makedirs(DATEN, exist_ok=True)

with open(os.path.join(BASIS, "config.example.json"), encoding="utf-8") as f:
    _standard = json.load(f)
try:
    with open(os.path.join(BASIS, "config.json"), encoding="utf-8") as f:
        _eigene = json.load(f)
except FileNotFoundError:
    raise SystemExit("config.json fehlt — kopiere config.example.json nach config.json und trage "
                     "deine Zugaenge ein (oder lass Claude Code die Einrichtung machen, siehe SETUP.md).")

K = {**_standard, **_eigene}


def get(name: str):
    return K.get(name)


def datei(name: str) -> str:
    """Pfad einer Datei im Ordner daten/ (Gedaechtnis, Timer, Gespraeche ...)."""
    return os.path.join(DATEN, name)


def laden(name: str, standard):
    try:
        with open(datei(name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return standard


def speichern(name: str, daten) -> None:
    """Erst in eine Hilfsdatei, dann umbenennen — so ist die Datei nie halb geschrieben."""
    tmp = datei(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    os.replace(tmp, datei(name))
