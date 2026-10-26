"""Jarvis starten.

  python3 jarvis.py            normal: Mikrofon, Stimme, Fenster, Telegram
  python3 jarvis.py --text     nur Text im Terminal (zum Ausprobieren ohne Mikrofon)
  python3 jarvis.py --ohne-mikro   Fenster und Telegram, aber kein Zuhoeren

Das Fenster mit dem Gesicht: http://localhost:8340 (Port in config.json).
"""

import asyncio
import json
import os
import sys

import konfig

ABSCHIED = ("danke", "das war's", "das wars", "tschüss", "tschuess", "gute nacht", "bis später")


async def _textmodus() -> None:
    import gehirn
    print(f"{konfig.get('name')} im Textmodus — leere Zeile beendet.")
    while True:
        frage = (await asyncio.to_thread(input, "Du: ")).strip()
        if not frage:
            return
        print(f"{konfig.get('name')}: {await gehirn.antworten(frage, kanal='terminal')}\n")


def main() -> None:
    if "--text" in sys.argv:
        asyncio.run(_textmodus())
        return

    from contextlib import asynccontextmanager

    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, Response
    from fastapi.staticfiles import StaticFiles

    import gehirn
    import gesicht
    import ohr
    import ruhe
    import stimme
    import telegram_bot
    import termine

    @asynccontextmanager
    async def lebenszeit(_app):
        await start()
        yield

    app = FastAPI(lifespan=lebenszeit)
    fenster: set[WebSocket] = set()
    vorne = os.path.join(konfig.BASIS, "frontend")
    app.mount("/static", StaticFiles(directory=vorne), name="static")
    schleife: asyncio.AbstractEventLoop | None = None
    sperre = asyncio.Lock()            # eine Sprachfrage nach der anderen

    async def an_fenster(art: str, text: str) -> None:
        for ws in list(fenster):
            try:
                await ws.send_text(json.dumps({"art": art, "text": text}))
            except Exception:
                fenster.discard(ws)

    async def sprachfrage(text: str, folgefrage: bool = False) -> None:
        async with sperre:
            gesicht.setze_zustand("denkt")
            try:
                antwort = await gehirn.antworten(text, kanal="sprache", folgefrage=folgefrage)
            except Exception as e:
                print(f"[jarvis] Antwort fehlgeschlagen: {e!r}", flush=True)
                antwort = "Entschuldigung, da ist etwas schiefgegangen."
            if not antwort:                  # Fernseher o.ae., nicht an Jarvis gerichtet
                gesicht.setze_zustand("ruhe")
                return
            await an_fenster("du", text)
            await an_fenster("jarvis", antwort)
            await stimme.sprechen(antwort)
            if not any(w in text.lower() for w in ABSCHIED):
                ohr.folgefrage_erlauben()

    async def melden(text: str) -> None:
        """Timer/Erinnerung: laut sagen (ausser in Nachtruhe/Ruhemodus), immer auch per Telegram."""
        await an_fenster("jarvis", text)
        await telegram_bot.senden("⏰ " + text)
        if not ruhe.still():
            async with sperre:
                await stimme.sprechen(text)

    @app.get("/")
    async def startseite():
        return FileResponse(os.path.join(vorne, "index.html"))

    @app.get("/api/gesicht")
    async def gesicht_bild():
        return Response(gesicht.bild(), media_type="application/octet-stream",
                        headers={"Cache-Control": "no-store"})

    @app.post("/api/zuhoeren")
    async def zuhoeren():
        """Klick aufs Gesicht: zuhoeren wie nach "Hey Jarvis"."""
        ohr.jetzt_zuhoeren()
        gesicht.setze_zustand("hoert")
        return {"ok": True}

    @app.websocket("/ws")
    async def ws_verbindung(ws: WebSocket):
        await ws.accept()
        fenster.add(ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            fenster.discard(ws)

    async def start():
        nonlocal schleife
        schleife = asyncio.get_running_loop()
        gesicht.starten()
        if "--ohne-mikro" not in sys.argv:
            ohr.starten(lambda text, folge: asyncio.run_coroutine_threadsafe(sprachfrage(text, folge), schleife))
        asyncio.create_task(telegram_bot.schleife())
        asyncio.create_task(termine.schleife(melden))
        print(f"[jarvis] Fenster: http://localhost:{konfig.get('port')}", flush=True)

    uvicorn.run(app, host="127.0.0.1", port=int(konfig.get("port") or 8340), log_level="warning")


if __name__ == "__main__":
    main()
