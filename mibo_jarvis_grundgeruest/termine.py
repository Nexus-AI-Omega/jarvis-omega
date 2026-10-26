"""Timer und Erinnerungen.

Beides liegt in daten/termine.json und uebersteht so einen Neustart. Eine
Schleife prueft jede Sekunde, ob etwas faellig ist, und uebergibt es an
melden(text) — server.py entscheidet, ob Jarvis es sagt oder per Telegram
schickt (Nachtruhe).
"""

import asyncio
import re
import time
import uuid
from datetime import datetime

import konfig


def _alle() -> list[dict]:
    return konfig.laden("termine.json", [])


def _speichern(liste: list[dict]) -> None:
    konfig.speichern("termine.json", sorted(liste, key=lambda t: t["faellig"]))


def timer_stellen(sekunden: int, name: str = "") -> str:
    if sekunden <= 0:
        return "Die Dauer muss groesser als null sein."
    t = {"id": uuid.uuid4().hex[:6], "art": "timer", "faellig": time.time() + sekunden,
         "text": name.strip()}
    _speichern(_alle() + [t])
    dauer = f"{sekunden // 60} Minute(n)" + (f" {sekunden % 60} Sekunden" if sekunden % 60 else "") \
        if sekunden >= 60 else f"{sekunden} Sekunden"
    return f"Timer{f' {chr(39)}' + t['text'] + chr(39) if t['text'] else ''} gestellt: {dauer}."


def erinnerung_stellen(zeitpunkt: str, text: str) -> str:
    """zeitpunkt im Format JJJJ-MM-TT HH:MM (das Sprachmodell rechnet "morgen um 8" selbst um)."""
    try:
        wann = datetime.strptime(zeitpunkt.strip(), "%Y-%m-%d %H:%M").timestamp()
    except ValueError:
        return "Zeitpunkt bitte als JJJJ-MM-TT HH:MM."
    if wann <= time.time():
        return "Dieser Zeitpunkt liegt in der Vergangenheit."
    t = {"id": uuid.uuid4().hex[:6], "art": "erinnerung", "faellig": wann, "text": text.strip()}
    _speichern(_alle() + [t])
    return f"Erinnerung fuer {datetime.fromtimestamp(wann).strftime('%d.%m. %H:%M')} gespeichert."


def liste() -> str:
    alle = _alle()
    if not alle:
        return "Keine Timer oder Erinnerungen."
    zeilen = []
    for t in alle:
        rest = int(t["faellig"] - time.time())
        wann = (f"noch {rest // 60} min {rest % 60} s" if t["art"] == "timer"
                else datetime.fromtimestamp(t["faellig"]).strftime("%d.%m. %H:%M"))
        zeilen.append(f"[{t['id']}] {t['art']}: {t['text'] or 'ohne Namen'} – {wann}")
    return "\n".join(zeilen)


def loeschen(stichwort: str) -> str:
    alle = _alle()
    rest = [t for t in alle if stichwort not in t["id"] and stichwort.lower() not in t["text"].lower()]
    if len(rest) == len(alle):
        return "Nichts Passendes gefunden."
    _speichern(rest)
    return f"{len(alle) - len(rest)} geloescht."


async def schleife(melden) -> None:
    """melden(text) -> awaitable. Laeuft fuer immer."""
    while True:
        jetzt = time.time()
        alle = _alle()
        faellig = [t for t in alle if t["faellig"] <= jetzt]
        if faellig:
            _speichern([t for t in alle if t["faellig"] > jetzt])
            for t in faellig:
                spaet = jetzt - t["faellig"] > 120      # Jarvis lief zum Zeitpunkt nicht
                if t["art"] == "timer":
                    text = f"Der Timer für {t['text']} ist abgelaufen." if t["text"] else "Der Timer ist abgelaufen."
                else:
                    text = f"Erinnerung: {t['text']}"
                if spaet:
                    text += f" (eigentlich fällig um {time.strftime('%H:%M', time.localtime(t['faellig']))})"
                try:
                    await melden(re.sub(r"\s+", " ", text))
                except Exception as e:
                    print(f"[termine] Melden fehlgeschlagen: {e!r}", flush=True)
        await asyncio.sleep(1)
