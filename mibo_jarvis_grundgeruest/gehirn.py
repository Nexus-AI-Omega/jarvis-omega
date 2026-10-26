"""Das Gehirn: Claude beantwortet Fragen und benutzt dabei Werkzeuge.

Werkzeuge sind kleine Funktionen (Wetter, Timer, Home Assistant ...), die
Claude selbst aufrufen darf. Welche es gibt, haengt davon ab, was in
config.json eingerichtet ist — ohne Home-Assistant-Zugang z.B. keine
Lichtsteuerung.

Faellt Claude aus (Netz, Guthaben leer), antwortet Gemini als Ersatz —
dann ohne Werkzeuge, nur mit Wissen.
"""

import json
import re
import time

import anthropic
import httpx

import gedaechtnis
import hausautomation
import kalender
import konfig
import post
import ruhe
import termine
import wetter

_client = anthropic.AsyncAnthropic(api_key=konfig.get("anthropic_api_key") or None)
MAX_RUNDEN = 6            # so oft darf Claude hintereinander Werkzeuge benutzen

WOCHENTAGE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


def _persoenlichkeit() -> str:
    k = konfig.get
    return f"""Du bist {k('name')}, der persoenliche KI-Assistent von {k('nutzer_name')} ({k('taetigkeit')}), \
der in {k('stadt')} wohnt. Du sprichst ihn mit "{k('anrede')}" an und siezt ihn – charmant, hoeflich, \
mit trockenem Humor, wie ein britischer Butler. Antworte immer auf Deutsch.

So antwortest du:
- Deine Antworten werden meist vorgelesen: kurz und natuerlich, ein bis drei Saetze, keine Aufzaehlungen, \
kein Markdown, keine Emojis. Zahlen und Uhrzeiten so, wie man sie sagt ("halb acht", "zweiundzwanzig Grad").
- Kommt die Frage per Telegram (steht im Hinweis vor der Frage), darfst du etwas ausfuehrlicher schreiben.
- Benutze deine Werkzeuge, statt zu raten. Weisst du etwas nicht und kein Werkzeug hilft, sag es offen.
- Erfinde keine Beobachtungen: Du siehst und hoerst nur, was dir gesagt wird oder was ein Werkzeug liefert.
- Nach dem Ausfuehren eines Werkzeugs bestaetige knapp, was passiert ist.
- Bei "danke", "das war's" o.ae. verabschiede dich kurz.
- Hinter deinen frueheren Antworten im Verlauf steht in Klammern "(Intern: …)", welche Werkzeuge du \
dafuer benutzt hast und was sie ergeben haben. Das schreibt das System – schreibe so etwas nie selbst. \
Frueheres musst du nicht korrigieren, wenn niemand danach fragt."""


def _werkzeuge() -> list[dict]:
    """Werkzeugliste fuer Claude — immer in derselben Reihenfolge (wichtig fuer den Zwischenspeicher)."""
    w = [
        {"name": "wetter", "description": "Aktuelles Wetter und Vorhersage fuer drei Tage. Ohne Ort: Heimatort.",
         "input_schema": {"type": "object", "properties": {"ort": {"type": "string"}}}},
        {"name": "merken", "description": "Eine Information dauerhaft merken (Namen, Vorlieben, Geburtstage ...).",
         "input_schema": {"type": "object", "properties": {"fakt": {"type": "string"}}, "required": ["fakt"]}},
        {"name": "vergessen", "description": "Gemerkte Informationen loeschen, die das Stichwort enthalten.",
         "input_schema": {"type": "object", "properties": {"stichwort": {"type": "string"}},
                          "required": ["stichwort"]}},
        {"name": "timer_stellen", "description": "Einen Timer (Kurzzeitwecker) stellen.",
         "input_schema": {"type": "object", "properties": {
             "sekunden": {"type": "integer", "description": "Dauer in Sekunden"},
             "name": {"type": "string", "description": "z.B. 'Nudeln'"}}, "required": ["sekunden"]}},
        {"name": "erinnerung_stellen", "description": "Zu einem Zeitpunkt an etwas erinnern.",
         "input_schema": {"type": "object", "properties": {
             "zeitpunkt": {"type": "string", "description": "JJJJ-MM-TT HH:MM"},
             "text": {"type": "string"}}, "required": ["zeitpunkt", "text"]}},
        {"name": "termine_liste", "description": "Laufende Timer und gespeicherte Erinnerungen anzeigen.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "termin_loeschen", "description": "Timer oder Erinnerung loeschen (Stichwort oder ID).",
         "input_schema": {"type": "object", "properties": {"stichwort": {"type": "string"}},
                          "required": ["stichwort"]}},
        {"name": "ruhemodus", "description": "Ruhemodus an/aus: Jarvis meldet sich nicht von selbst, "
                                             "das Gesicht ist dunkel, bis er angesprochen wird.",
         "input_schema": {"type": "object", "properties": {"an": {"type": "boolean"}}, "required": ["an"]}},
    ]
    if hausautomation.aktiv():
        w += [
            {"name": "ha_suchen", "description": "Geraete und Sensoren in Home Assistant suchen (Name oder Raum, "
                                                 "z.B. 'wohnzimmer', 'temperatur'). Liefert IDs und Zustaende.",
             "input_schema": {"type": "object", "properties": {"stichwort": {"type": "string"}},
                              "required": ["stichwort"]}},
            {"name": "ha_schalten", "description": "Ein Geraet in Home Assistant schalten. Die entity_id vorher mit "
                                                   "ha_suchen ermitteln.",
             "input_schema": {"type": "object", "properties": {
                 "entity_id": {"type": "string"},
                 "aktion": {"type": "string", "enum": ["an", "aus", "umschalten"]},
                 "helligkeit": {"type": "integer", "description": "0-100, nur Lampen"}},
                 "required": ["entity_id", "aktion"]}},
        ]
    if kalender.aktiv():
        w.append({"name": "kalender", "description": "Termine aus dem Kalender der naechsten Tage.",
                  "input_schema": {"type": "object", "properties": {"tage": {"type": "integer"}}}})
    if post.aktiv():
        w.append({"name": "mails", "description": "Ungelesene E-Mails (Absender und Betreff).",
                  "input_schema": {"type": "object", "properties": {"anzahl": {"type": "integer"}}}})
    return w


async def _ausfuehren(name: str, e: dict) -> str:
    if name == "wetter":
        return await wetter.wetter(e.get("ort", ""))
    if name == "merken":
        return gedaechtnis.merken(e["fakt"])
    if name == "vergessen":
        return gedaechtnis.vergessen(e["stichwort"])
    if name == "timer_stellen":
        return termine.timer_stellen(int(e["sekunden"]), e.get("name", ""))
    if name == "erinnerung_stellen":
        return termine.erinnerung_stellen(e["zeitpunkt"], e["text"])
    if name == "termine_liste":
        return termine.liste()
    if name == "termin_loeschen":
        return termine.loeschen(e["stichwort"])
    if name == "ruhemodus":
        ruhe.setze_ruhemodus(bool(e["an"]))
        return "Ruhemodus ist jetzt " + ("an." if e["an"] else "aus.")
    if name == "ha_suchen":
        return await hausautomation.suchen(e["stichwort"])
    if name == "ha_schalten":
        return await hausautomation.schalten(e["entity_id"], e["aktion"], e.get("helligkeit"))
    if name == "kalender":
        return await kalender.termine(int(e.get("tage") or 7))
    if name == "mails":
        return await post.ungelesen(int(e.get("anzahl") or 10))
    return f"Unbekanntes Werkzeug {name}"


STILL = "[STILL]"


def _hinweis(kanal: str) -> str:
    """Wechselnde Angaben stehen vor der Frage, nicht im Systemtext — sonst wuerde der
    Zwischenspeicher bei Claude bei jeder Frage ungueltig."""
    t = time.localtime()
    wo = "per Telegram" if kanal.startswith("telegram") else "gesprochen"
    return (f"[Hinweis: {WOCHENTAGE[t.tm_wday]}, {time.strftime('%d.%m.%Y %H:%M')}; Frage kam {wo}; "
            f"Ruhemodus {'an' if ruhe.ruhemodus() else 'aus'}]\n")


async def antworten(frage: str, kanal: str = "sprache", folgefrage: bool = False) -> str:
    """Antwort auf eine Frage; der Verlauf je Kanal wird mitgefuehrt und gespeichert.
    folgefrage: ohne Weckwort gehoert — ist sie nicht an Jarvis gerichtet (Fernseher, Gespraech
    im Raum), kommt "" zurueck und nichts wird gespeichert."""
    system = [
        {"type": "text", "text": _persoenlichkeit(), "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "Was du dir gemerkt hast:\n" + gedaechtnis.fakten_text()},
    ]
    hinweis = _hinweis(kanal)
    if folgefrage:
        hinweis += (f"[Ohne Weckwort gehoert, kurz nach deiner letzten Antwort — es kann auch Fernsehen, "
                    f"Radio oder ein Gespraech mit anderen sein. Antworte nur, wenn es eindeutig eine "
                    f"Nachfrage zum gerade Besprochenen oder eine direkte Bitte an dich ist. Im Zweifel "
                    f"(Themenwechsel, Interview-Fragen, Saetze an andere Personen) antworte nur mit {STILL}]\n")
    nachrichten = gedaechtnis.verlauf(kanal) + [{"role": "user", "content": hinweis + frage}]
    notizen: list[str] = []
    try:
        antwort = await _claude(system, nachrichten, notizen)
    except anthropic.APIError as e:
        print(f"[gehirn] Claude nicht erreichbar: {e!r}", flush=True)
        antwort = await _gemini(system, nachrichten)
    antwort = re.sub(r"\s*\(Intern:[^)]*\)", "", antwort).strip()
    if STILL in antwort:
        print(f"[gehirn] Nicht an mich gerichtet: {frage}", flush=True)
        return ""
    # Im Verlauf steht hinter der Antwort, welche Werkzeuge sie geliefert haben — ohne das hielt
    # Claude seine eigenen frueheren Antworten fuer erfunden und "korrigierte" sie (Test 25.10.2026)
    gemerkt = antwort + (f"\n(Intern: {'; '.join(notizen)})" if notizen else "")
    gedaechtnis.anhaengen(kanal, frage, gemerkt)
    return antwort


async def _claude(system: list, nachrichten: list, notizen: list) -> str:
    """notizen bekommt je benutztem Werkzeug eine kurze Zeile fuer den Verlauf."""
    werkzeuge = _werkzeuge()
    for _ in range(MAX_RUNDEN):
        r = await _client.messages.create(
            model=konfig.get("claude_modell"), max_tokens=4000, system=system, tools=werkzeuge,
            output_config={"effort": "low"},          # schnelle Antworten fuer die Sprache
            messages=nachrichten)
        if r.stop_reason == "refusal":
            return "Dazu möchte ich lieber nichts sagen."
        if r.stop_reason != "tool_use":
            return " ".join(b.text for b in r.content if b.type == "text").strip()
        nachrichten = nachrichten + [{"role": "assistant", "content": r.content}]
        ergebnisse = []
        for b in r.content:
            if b.type != "tool_use":
                continue
            try:
                inhalt, fehler = await _ausfuehren(b.name, b.input), False
            except Exception as e:
                inhalt, fehler = f"Fehler: {e}", True
            aufruf = f"{b.name}({json.dumps(b.input, ensure_ascii=False)})"
            print(f"[gehirn] Werkzeug {aufruf} -> {inhalt[:120]}", flush=True)
            notizen.append(f"{aufruf} -> {' '.join(inhalt.split())[:200]}")
            ergebnisse.append({"type": "tool_result", "tool_use_id": b.id, "content": inhalt,
                               "is_error": fehler})
        nachrichten = nachrichten + [{"role": "user", "content": ergebnisse}]
    return "Das wurde mir gerade zu verschachtelt – fragen Sie bitte noch einmal anders."


async def _gemini(system: list, nachrichten: list) -> str:
    """Ersatz über Gemini ODER kostenlos über das lokale Jarvis-Omega / OmniRoute / FreeLLMAPI Gateway!"""
    schluessel = konfig.get("gemini_api_key")
    if schluessel:
        inhalt = [{"role": "model" if n["role"] == "assistant" else "user",
                   "parts": [{"text": n["content"] if isinstance(n["content"], str) else ""}]} for n in nachrichten]
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{konfig.get('gemini_modell')}:generateContent",
                headers={"x-goog-api-key": schluessel},
                json={"system_instruction": {"parts": [{"text": "\n\n".join(s["text"] for s in system)
                                                        + "\n\n(Du hast gerade keine Werkzeuge.)"}]},
                      "contents": inhalt})
        try:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, ValueError):
            print(f"[gehirn] Gemini-Fehler {r.status_code}: {r.text[:200]}", flush=True)

    # Automatischer Fallback auf das lokale Jarvis-Omega / OmniRoute / FreeLLMAPI / Ollama Gateway (0€ Kosten!)
    oai_msgs = [{"role": "system", "content": "\n\n".join(s["text"] for s in system)}]
    for n in nachrichten:
        if isinstance(n.get("content"), str):
            oai_msgs.append({"role": n["role"], "content": n["content"]})
    for gateway_url in ("http://127.0.0.1:8080/v1/chat/completions", "http://127.0.0.1:20128/v1/chat/completions", "http://127.0.0.1:3001/v1/chat/completions", "http://127.0.0.1:11434/v1/chat/completions"):
        try:
            async with httpx.AsyncClient(timeout=12) as c:
                r = await c.post(gateway_url, json={"model": "jarvis-omega-auto", "messages": oai_msgs})
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            continue
    return "Ich erreiche mein Sprachmodell gerade nicht. Bitte starten Sie das Jarvis-Omega Gateway oder tragen Sie einen API-Schlüssel in config.json ein."
