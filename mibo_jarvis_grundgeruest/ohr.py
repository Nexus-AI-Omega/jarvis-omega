"""Zuhoeren: Weckwort "Hey Jarvis", Aufnahme bis zur Sprechpause, Spracherkennung.

Ablauf in einem eigenen Thread:
  1. openWakeWord hoert auf "Hey Jarvis" (fertig trainiertes Modell, laeuft lokal).
  2. Danach wird aufgenommen, bis eine knappe Sekunde Ruhe ist (hoechstens 15 s).
  3. faster-whisper macht daraus Text — ebenfalls lokal, ohne Cloud.
  4. Nach einer Antwort darf man kurz ohne "Hey Jarvis" weiterreden (Folgefrage).

Waehrend Jarvis spricht (stimme.spricht), wird nichts ausgewertet.
"""

import queue
import threading
import time

import numpy as np
import sounddevice as sd

import gesicht
import konfig
import stimme

RATE = 16000
FRAME = 1280                  # 80 ms — so erwartet es openWakeWord
STILLE_S = 0.9                # so lange Ruhe beendet die Aufnahme
MAX_S = 15
WARTEN_AUF_SPRACHE_S = 5      # nach "Hey Jarvis" so lange auf den ersten Ton warten

# Whisper erfindet bei Rauschen gern Saetze aus Untertiteln. Solche Ergebnisse
# sind keine echte Frage und werden verworfen.
RAUSCH_SAETZE = {
    "untertitel im auftrag des zdf", "untertitel von stephanie geiges", "vielen dank.",
    "vielen dank fürs zuhören.", "danke.", "danke fürs zuschauen.", "das war's für heute.",
    "bis zum nächsten mal.", "mhm.", "so.", ".",
}

_frames: queue.Queue = queue.Queue(maxsize=200)
_folge_bis = 0.0
_bei_text = None
_modell = None


_klick_bis = 0.0


def jetzt_zuhoeren() -> None:
    """Klick aufs Gesicht: zuhoeren wie nach "Hey Jarvis" (das ist sicher an Jarvis gerichtet)."""
    global _klick_bis
    _klick_bis = time.time() + float(konfig.get("folgefrage_sekunden") or 8)


def folgefrage_erlauben() -> None:
    """Nach einer Antwort: die naechsten Sekunden ohne Weckwort zuhoeren."""
    global _folge_bis
    _folge_bis = time.time() + float(konfig.get("folgefrage_sekunden") or 0)


def _rms(f: np.ndarray) -> float:
    return float(np.sqrt(np.mean(f.astype(np.float32) ** 2)))


def _mikro(indata, frames, zeit, status) -> None:
    try:
        _frames.put_nowait(indata[:, 0].copy())
    except queue.Full:
        pass                                   # lieber ein Stueck verlieren als zu spaet sein


def erkennen(ton: np.ndarray) -> str:
    """16-kHz-Ton (int16) -> Text. Auch fuer Telegram-Sprachnachrichten."""
    global _modell
    if _modell is None:
        from faster_whisper import WhisperModel
        _modell = WhisperModel(konfig.get("whisper_modell") or "small", device="cpu", compute_type="int8")
    teile, _ = _modell.transcribe(ton.astype(np.float32) / 32768.0, language="de", beam_size=5,
                                  vad_filter=True, condition_on_previous_text=False,
                                  initial_prompt=f"Hey {konfig.get('name')}.")
    text = " ".join(t.text.strip() for t in teile).strip()
    if text.lower().rstrip("!") in RAUSCH_SAETZE or any(r in text.lower() for r in ("untertitel", "zdf")):
        return ""
    return text


def _echo(text: str) -> bool:
    """Ist das Gehoerte nur Jarvis' eigener letzter Satz aus dem Lautsprecher?"""
    def kern(t):
        return " ".join("".join(c for c in t.lower() if c.isalnum() or c == " ").split())
    t, gesagt = kern(text), kern(stimme.zuletzt_gesagt)
    return len(t) > 3 and t in gesagt


def _aufnehmen(warten_s: float, rauschen: float, erster: np.ndarray | None = None) -> np.ndarray | None:
    """Aufnahme bis zur Sprechpause. None, wenn in warten_s niemand spricht.
    erster: schon gelesener Block, mit dem die Aufnahme beginnt (Folgefrage)."""
    schwelle = max(rauschen * 3, 400)
    teile, vorlauf = [], []
    gesprochen, ruhig_seit = False, None
    start = time.time()
    while True:
        f, erster = (erster, None) if erster is not None else (_frames.get(), None)
        laut = _rms(f) > schwelle
        if not gesprochen:
            vorlauf = (vorlauf + [f])[-4:]        # 0,3 s vor dem ersten Ton behalten
            if laut:
                gesprochen, teile = True, list(vorlauf)
            elif time.time() - start > warten_s:
                return None
            continue
        teile.append(f)
        if laut:
            ruhig_seit = None
        elif ruhig_seit is None:
            ruhig_seit = time.time()
        elif time.time() - ruhig_seit > STILLE_S:
            break
        if len(teile) * FRAME / RATE > MAX_S:
            break
    return np.concatenate(teile)


def _schleife() -> None:
    try:
        _hoeren()
    except Exception as e:
        print(f"[ohr] Zuhoeren nicht moeglich: {e!r} — Mikrofon pruefen (config.json \"mikrofon\").",
              flush=True)


def _hoeren() -> None:
    global _klick_bis
    import openwakeword.utils
    from openwakeword.model import Model
    openwakeword.utils.download_models(["hey_jarvis"])     # beim ersten Start, danach schon da
    weckwort = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    schwelle = float(konfig.get("weckwort_schwelle") or 0.5)
    rauschen = 300.0
    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=FRAME,
                        device=konfig.get("mikrofon") or None, callback=_mikro):
        print(f"[ohr] Hoere auf \"Hey {konfig.get('name')}\"", flush=True)
        while True:
            f = _frames.get()
            if stimme.spricht.is_set():
                weckwort.reset()
                while not _frames.empty():          # was waehrend des Sprechens aufgelaufen ist, weg
                    _frames.get_nowait()
                continue
            r = _rms(f)
            if r < rauschen * 2:                         # Grundrauschen des Raums langsam mitfuehren
                rauschen = rauschen * 0.98 + r * 0.02
            klick = time.time() < _klick_bis
            folge = klick or time.time() < _folge_bis
            if not folge and weckwort.predict(f)["hey_jarvis"] < schwelle:
                continue
            if folge and r < max(rauschen * 3, 400):
                continue
            # angesprochen (oder Folgefrage begonnen): aufnehmen
            gesicht.setze_zustand("hoert")
            ton = _aufnehmen(1.0 if folge else WARTEN_AUF_SPRACHE_S, rauschen, f if folge else None)
            weckwort.reset()
            _klick_bis = 0.0
            if ton is None:
                gesicht.setze_zustand("ruhe")
                continue
            gesicht.setze_zustand("denkt")
            text = erkennen(ton)
            # "Hey Jarvis" selbst gehoert nicht zur Frage
            name = konfig.get("name") or "Jarvis"
            for vorne in (f"hey {name.lower()}", name.lower()):
                if text.lower().startswith(vorne):
                    text = text[len(vorne):].lstrip(" ,.!?")
                    break
            if not text or (folge and _echo(text)):
                if text:
                    print(f"[ohr] Eigenes Echo verworfen: {text}", flush=True)
                gesicht.setze_zustand("ruhe")
                continue
            print(f"[ohr] Gehoert{' (Folgefrage)' if folge and not klick else ''}: {text}", flush=True)
            _bei_text(text, folge and not klick)
            # was waehrend der Erkennung aufgelaufen ist, ist alt
            while not _frames.empty():
                _frames.get_nowait()


def starten(bei_text) -> None:
    """bei_text(text, folgefrage) wird im Ohr-Thread aufgerufen — muss thread-sicher sein.
    folgefrage: ohne Weckwort gehoert, kann also auch Fernsehen oder ein Gespraech im Raum sein."""
    global _bei_text
    _bei_text = bei_text
    threading.Thread(target=_schleife, name="ohr", daemon=True).start()
