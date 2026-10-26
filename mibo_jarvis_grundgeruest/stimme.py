"""Sprechen mit der ElevenLabs-Stimme.

Die Antwort wird in Saetze geteilt: Waehrend der erste Satz schon zu hoeren
ist, wird der naechste erzeugt — so beginnt Jarvis schneller zu sprechen.
ElevenLabs liefert rohe Tondaten (PCM, 22050 Hz), die direkt ueber den
Lautsprecher laufen; aus ihrer Lautstaerke bewegt sich der Mund im Gesicht.

Solange Jarvis spricht, ist `spricht` gesetzt — ohr.py hoert dann nicht zu,
sonst wuerde er sich selbst antworten.
"""

import asyncio
import re
import threading

import httpx
import numpy as np
import sounddevice as sd

import gesicht
import konfig

RATE = 22050
BLOCK = 1024          # ca. 46 ms je Block — so oft bekommt der Mund einen neuen Wert

spricht = threading.Event()
zuletzt_gesagt = ""      # ohr.py verwirft es, falls das Mikrofon den eigenen Satz noch hoert
_http = httpx.AsyncClient(timeout=30)


def _saetze(text: str) -> list[str]:
    """In Saetze teilen; sehr kurze Stuecke an den Vorgaenger haengen (klingt sonst abgehackt)."""
    teile = [t.strip() for t in re.split(r"(?<=[.!?…])\s+", text.strip()) if t.strip()]
    out: list[str] = []
    for t in teile:
        if out and len(out[-1]) < 40:
            out[-1] += " " + t
        else:
            out.append(t)
    return out


async def _erzeugen(satz: str) -> bytes:
    stimme = konfig.get("elevenlabs_stimme")
    r = await _http.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{stimme}?output_format=pcm_{RATE}",
        headers={"xi-api-key": konfig.get("elevenlabs_api_key"), "Content-Type": "application/json"},
        json={"text": satz, "model_id": konfig.get("elevenlabs_modell"), "language_code": "de",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.85}})
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    return r.content


def _abspielen(pcm: bytes) -> None:
    """Blockiert, bis der Ton durch ist; setzt nebenbei die Mundoeffnung."""
    ton = np.frombuffer(pcm, dtype=np.int16)
    if not len(ton):
        return
    spitze = float(np.percentile(np.abs(ton), 98)) or 1.0
    with sd.OutputStream(samplerate=RATE, channels=1, dtype="int16",
                         device=konfig.get("lautsprecher") or None) as aus:
        for i in range(0, len(ton), BLOCK):
            stueck = ton[i:i + BLOCK]
            pegel = float(np.sqrt(np.mean(stueck.astype(np.float32) ** 2))) / (spitze * 0.6)
            gesicht.setze_mund(pegel)
            aus.write(stueck)
    gesicht.setze_mund(0.0)


async def sprechen(text: str) -> None:
    """Text vorlesen. Ohne ElevenLabs-Zugang steht die Antwort nur im Fenster."""
    if not text.strip():
        return
    if not (konfig.get("elevenlabs_api_key") and konfig.get("elevenlabs_stimme")):
        print("[stimme] Keine ElevenLabs-Stimme eingerichtet — Antwort nur als Text.", flush=True)
        return
    global zuletzt_gesagt
    zuletzt_gesagt = text
    spricht.set()
    gesicht.setze_zustand("spricht")
    try:
        saetze = _saetze(text)
        naechster = asyncio.create_task(_erzeugen(saetze[0]))
        for i in range(len(saetze)):
            pcm = await naechster
            if i + 1 < len(saetze):
                naechster = asyncio.create_task(_erzeugen(saetze[i + 1]))
            await asyncio.to_thread(_abspielen, pcm)
    except Exception as e:
        print(f"[stimme] Sprechen fehlgeschlagen: {e!r}", flush=True)
    finally:
        # Der Lautsprecher spielt mit Verzoegerung (Puffer im Tonsystem), dazu Raumhall:
        # erst danach wieder zuhoeren (beim Test am 25.10.2026 kam sonst der letzte Satz zurueck)
        await asyncio.sleep(1.0)
        spricht.clear()
        gesicht.setze_zustand("ruhe")
