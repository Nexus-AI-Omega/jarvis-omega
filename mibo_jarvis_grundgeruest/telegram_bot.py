"""Telegram: mit Jarvis schreiben oder Sprachnachrichten schicken — auch unterwegs.

Einrichten: in Telegram mit @BotFather einen Bot anlegen, den Token in
config.json "telegram_bot_token" eintragen. Schreibt man dem Bot dann, antwortet
er mit der Chat-Nummer — die kommt in "telegram_chat_ids". Nur diese Chats
duerfen Jarvis benutzen; alle anderen bekommen keine Antwort.
"""

import asyncio
import subprocess

import httpx
import numpy as np

import gehirn
import konfig
import ohr

API = "https://api.telegram.org/bot{token}/{methode}"


def aktiv() -> bool:
    return bool(konfig.get("telegram_bot_token"))


def _erlaubt(chat_id: int) -> bool:
    return chat_id in {int(c) for c in konfig.get("telegram_chat_ids") or []}


async def _aufruf(c: httpx.AsyncClient, methode: str, **daten):
    r = await c.post(API.format(token=konfig.get("telegram_bot_token"), methode=methode), json=daten)
    return r.json()


async def senden(text: str, chat_id: int | None = None) -> None:
    """An einen Chat oder (ohne chat_id) an alle freigeschalteten Chats."""
    if not aktiv():
        return
    ziele = [chat_id] if chat_id else [int(c) for c in konfig.get("telegram_chat_ids") or []]
    async with httpx.AsyncClient(timeout=30) as c:
        for z in ziele:
            await _aufruf(c, "sendMessage", chat_id=z, text=text[:4000])


async def _sprachnachricht(c: httpx.AsyncClient, datei_id: str) -> str:
    info = await _aufruf(c, "getFile", file_id=datei_id)
    pfad = info["result"]["file_path"]
    r = await c.get(f"https://api.telegram.org/file/bot{konfig.get('telegram_bot_token')}/{pfad}")
    # Telegram schickt OGG/Opus — ffmpeg macht daraus 16 kHz Mono fuer Whisper
    pcm = subprocess.run(["ffmpeg", "-v", "quiet", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", "16000",
                          "pipe:1"], input=r.content, capture_output=True, timeout=60).stdout
    return await asyncio.to_thread(ohr.erkennen, np.frombuffer(pcm, dtype=np.int16))


async def _bearbeiten(c: httpx.AsyncClient, nachricht: dict) -> None:
    try:
        await _beantworten(c, nachricht)
    except Exception as e:
        print(f"[telegram] Nachricht nicht bearbeitet: {e!r}", flush=True)


async def _beantworten(c: httpx.AsyncClient, nachricht: dict) -> None:
    chat_id = nachricht["chat"]["id"]
    if not _erlaubt(chat_id):
        if nachricht.get("text", "").startswith("/start"):
            await _aufruf(c, "sendMessage", chat_id=chat_id,
                          text=f"Hallo! Deine Chat-Nummer ist {chat_id}. Trag sie in config.json bei "
                               f"\"telegram_chat_ids\" ein und starte Jarvis neu.")
        print(f"[telegram] Nachricht von nicht freigeschaltetem Chat {chat_id} ignoriert", flush=True)
        return
    text = nachricht.get("text", "")
    if "voice" in nachricht:
        text = await _sprachnachricht(c, nachricht["voice"]["file_id"])
        if not text:
            await _aufruf(c, "sendMessage", chat_id=chat_id, text="Das habe ich leider nicht verstanden.")
            return
        await _aufruf(c, "sendMessage", chat_id=chat_id, text=f"🎤 „{text}“")
    if not text or text.startswith("/start"):
        return
    await _aufruf(c, "sendChatAction", chat_id=chat_id, action="typing")
    antwort = await gehirn.antworten(text, kanal=f"telegram-{chat_id}")
    await _aufruf(c, "sendMessage", chat_id=chat_id, text=antwort[:4000])


async def schleife() -> None:
    """Holt neue Nachrichten per Long Polling (keine offene Verbindung von aussen noetig)."""
    if not aktiv():
        return
    print("[telegram] Bot aktiv", flush=True)
    versatz = 0
    async with httpx.AsyncClient(timeout=70) as c:
        while True:
            try:
                d = await _aufruf(c, "getUpdates", offset=versatz, timeout=50)
                for u in d.get("result", []):
                    versatz = u["update_id"] + 1
                    if "message" in u:
                        asyncio.create_task(_bearbeiten(c, u["message"]))
            except Exception as e:
                print(f"[telegram] {e!r} — neuer Versuch in 10 s", flush=True)
                await asyncio.sleep(10)
