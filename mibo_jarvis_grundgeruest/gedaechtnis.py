"""Was Jarvis sich merkt.

  * Fakten ("Merk dir, dass meine Frau Anna heisst") in daten/gedaechtnis.json —
    sie stehen bei jeder Frage mit im Hintergrundwissen.
  * Der Gespraechsverlauf je Kanal (Sprache, jeder Telegram-Chat) in
    daten/gespraeche.json, damit Jarvis nach einem Neustart weiss, worum es
    zuletzt ging. Gespeichert wird nur der Text, gekuerzt auf die letzten Wechsel.
"""

import time

import konfig

MAX_WECHSEL = 12          # so viele Frage-Antwort-Paare je Kanal
PAUSE_NEUES_GESPRAECH_S = 30 * 60


# ------------------------------------------------------------ Fakten
def fakten() -> list[dict]:
    return konfig.laden("gedaechtnis.json", [])


def merken(text: str) -> str:
    text = text.strip()
    alle = fakten()
    if any(f["text"].lower() == text.lower() for f in alle):
        return "Das weiss ich schon."
    alle.append({"text": text, "seit": time.strftime("%d.%m.%Y")})
    konfig.speichern("gedaechtnis.json", alle)
    return "Gemerkt."


def vergessen(stichwort: str) -> str:
    alle = fakten()
    rest = [f for f in alle if stichwort.lower() not in f["text"].lower()]
    if len(rest) == len(alle):
        return f"Zu '{stichwort}' habe ich nichts gespeichert."
    konfig.speichern("gedaechtnis.json", rest)
    return f"{len(alle) - len(rest)} Eintrag/Eintraege vergessen."


def fakten_text() -> str:
    alle = fakten()
    if not alle:
        return "(noch nichts)"
    return "\n".join(f"- {f['text']} (seit {f['seit']})" for f in alle)


# ------------------------------------------------------------ Gespraeche
def verlauf(kanal: str) -> list[dict]:
    """Bisherige Nachrichten des Kanals; nach langer Pause beginnt ein neues Gespraech."""
    g = konfig.laden("gespraeche.json", {}).get(kanal, {})
    if time.time() - g.get("zuletzt", 0) > PAUSE_NEUES_GESPRAECH_S:
        return []
    return g.get("nachrichten", [])


def anhaengen(kanal: str, frage: str, antwort: str) -> None:
    alle = konfig.laden("gespraeche.json", {})
    nachrichten = verlauf(kanal) + [{"role": "user", "content": frage},
                                    {"role": "assistant", "content": antwort}]
    alle[kanal] = {"zuletzt": time.time(), "nachrichten": nachrichten[-2 * MAX_WECHSEL:]}
    konfig.speichern("gespraeche.json", alle)
