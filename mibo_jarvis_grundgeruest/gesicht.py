"""Jarvis' Gesicht: ein 64x64-Pixelbild wie auf einer LED-Matrix.

Ein Thread zeichnet 20 Bilder pro Sekunde. Das Fenster (frontend/) holt sich
das jeweils neueste ueber /api/gesicht. Ist in config.json "matrix_ip" gesetzt,
geht dasselbe Bild zusaetzlich per DDP an eine WLED-Matrix (64x64 oder 16x16).

Zustaende: "ruhe" (blau, blinzelt, schaut ab und zu zur Seite), "hoert"
(etwas heller), "denkt" (gelb, Augen wandern), "spricht" (Mund folgt der
Lautstaerke). In der Nachtruhe und im Ruhemodus ist das Gesicht dunkel,
ausser Jarvis wird gerade angesprochen.
"""

import random
import socket
import threading
import time

import numpy as np

import konfig
import ruhe

N = 64
FPS = 20
BLAU = (40, 150, 255)
GELB = (255, 170, 0)
HELL_RUHE = 0.6
HELL_AKTIV = 1.0
WACH_S = 25          # so lange bleibt das Gesicht nach einem Gespraech nachts an

_lock = threading.Lock()
_zustand = "ruhe"
_mund = 0.0                 # 0 = Laecheln, 1 = weit offen (setzt stimme.py beim Sprechen)
_wach_bis = 0.0
_bild = bytes(N * N * 3)


def setze_zustand(z: str) -> None:
    global _zustand, _wach_bis
    with _lock:
        _zustand = z
        if z != "ruhe":
            _wach_bis = time.time() + WACH_S


def setze_mund(wert: float) -> None:
    global _mund
    _mund = max(0.0, min(1.0, wert))


def bild() -> bytes:
    """Aktuelles Bild: 64*64*3 Bytes RGB."""
    return _bild


# ------------------------------------------------------------ Zeichnen
Y, X = np.mgrid[0:N, 0:N].astype(np.float32)
AUGE_X = (19.5, 43.5)
AUGE_Y = 21.5
MUND_X = 31.5
LAECHELN_B = 19.5        # halbe Breite des Laechelns
OVAL_B = 12              # halbe Breite des offenen Mundes
LIPPE = 2.8


def _malen(img, alpha, farbe, f=1.0):
    a = np.clip(alpha, 0, 1)[..., None] * f
    np.maximum(img, a * np.asarray(farbe, np.float32), out=img)


def _kreis(cx, cy, r):
    return np.clip(r - np.hypot(X - cx, Y - cy) + 0.5, 0, 1)


def _rundrechteck(cx, cy, a, b, p=4.0):
    """Weiches abgerundetes Rechteck (Superellipse) mit Halbachsen a, b."""
    d = ((np.abs(X - cx) / max(a, 0.01)) ** p + (np.abs(Y - cy) / max(b, 0.01)) ** p) ** (1 / p)
    return np.clip((1 - d) * min(a, b) + 0.5, 0, 1)


def _strich(x0, y0, x1, y1, dicke):
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return np.clip(dicke / 2 - np.hypot(X - (x0 + t * dx), Y - (y0 + t * dy)) + 0.5, 0, 1)


def _mund_malen(img, mund, farbe):
    """Mund von 0 (Laecheln) bis 1 (weit offen) als eine Form: der Laechel-Bogen teilt sich in
    Ober- und Unterlippe, die beim Oeffnen auseinandergehen, waehrend der Mund schmaler wird."""
    s = min(mund / 0.35, 1.0)
    s = s * s * (3 - 2 * s)
    b = LAECHELN_B + (OVAL_B - LAECHELN_B) * s
    oben, unten = 40.0, 47 + mund * 9
    mitte, hoehe = (oben + unten) / 2, (unten - oben) / 2

    def lippen(u):
        bogen = 21 + np.sqrt(28 ** 2 - (u * LAECHELN_B) ** 2)
        rund = (1 - np.abs(u) ** 3) ** (1 / 3)
        return bogen + (mitte - hoehe * rund - bogen) * s, bogen + (mitte + hoehe * rund - bogen) * s

    us = np.linspace(-1, 1, 25)
    xs = MUND_X + us * b
    linie = np.zeros((N, N), np.float32)
    for y in lippen(us):
        for i in range(len(us) - 1):
            np.maximum(linie, _strich(xs[i], y[i], xs[i + 1], y[i + 1], LIPPE), out=linie)
    if s > 0:
        u = np.clip((X - MUND_X) / b, -1, 1)
        o, w = lippen(u)
        innen = np.clip(np.minimum(Y - o, w - Y) - LIPPE / 2 + 0.5, 0, 1) * (np.abs(X - MUND_X) < b)
        _malen(img, innen, farbe, 0.18)
    _malen(img, linie, farbe)


def zeichnen(blick=0.0, hoch=0.0, blinzeln=False, mund=0.0, denkt=False,
             farbe=BLAU, hell=1.0) -> np.ndarray:
    """Ein Bild (64, 64, 3) uint8. blick/hoch verschieben die Augen (Pixel)."""
    img = np.zeros((N, N, 3), np.float32)
    for ex in AUGE_X:
        cx = ex + blick
        if blinzeln:
            _malen(img, _rundrechteck(cx, AUGE_Y + 5 + hoch, 5, 1.3, p=2), farbe)
        else:
            _malen(img, _rundrechteck(cx, AUGE_Y + hoch, 4.8, 6.8), farbe)
            _malen(img, _kreis(cx - 1.5, AUGE_Y + hoch - 3, 1.1), (255, 255, 255), 0.35)
    if denkt:
        _malen(img, _strich(25, 46, 38, 46, 2.6), farbe)
    else:
        _mund_malen(img, mund, farbe)
    return np.clip(img * hell, 0, 255).astype(np.uint8)


# ------------------------------------------------------------ WLED-Matrix (optional)
_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
DDP_MAX = 480 * 3


def _an_matrix(ip: str, a: np.ndarray, seq: int, seite: int) -> None:
    """Bild per DDP (UDP 4048) an WLED; bei einer 16x16-Matrix wird verkleinert.
    Fuer LEDs stark gedimmt — sie sind viel heller als ein Bildschirm."""
    if seite != N:
        f = N // seite
        a = a.reshape(seite, f, seite, f, 3).max(axis=(1, 3))
    daten = (a.astype(np.float32) * 0.25).astype(np.uint8).tobytes()
    for off in range(0, len(daten), DDP_MAX):
        stueck = daten[off:off + DDP_MAX]
        letztes = off + DDP_MAX >= len(daten)
        kopf = bytes((0x41 if letztes else 0x40, seq, 0x01, 0x01)) + off.to_bytes(4, "big") \
            + len(stueck).to_bytes(2, "big")
        _sock.sendto(kopf + stueck, (ip, 4048))


def _matrix_seite(ip: str) -> int:
    import json
    import urllib.request
    try:
        info = json.loads(urllib.request.urlopen(f"http://{ip}/json/info", timeout=3).read())
        return 64 if info.get("leds", {}).get("matrix", {}).get("w", 16) >= 64 else 16
    except Exception:
        return 16


# ------------------------------------------------------------ Schleife
def _schleife() -> None:
    global _bild
    ip = konfig.get("matrix_ip") or ""
    seite = _matrix_seite(ip) if ip else 0
    seq = 0
    blinzeln_bis, naechstes_blinzeln = 0.0, time.time() + 3
    blick, blick_bis, naechster_blick = 0.0, 0.0, time.time() + 15
    mund_weich = 0.0
    while True:
        jetzt = time.time()
        if jetzt >= naechstes_blinzeln:
            blinzeln_bis, naechstes_blinzeln = jetzt + 0.15, jetzt + random.uniform(2.5, 6)
        if jetzt >= naechster_blick:
            blick = random.choice((-7.0, 7.0))
            blick_bis, naechster_blick = jetzt + 1.2, jetzt + random.uniform(12, 30)
        with _lock:
            z, wach = _zustand, jetzt < _wach_bis
        # Der Mund folgt der Lautstaerke weich (schnell auf, etwas langsamer zu), sonst zuckt er
        ziel = _mund if z == "spricht" else 0.0
        mund_weich += (ziel - mund_weich) * (0.65 if ziel > mund_weich else 0.4)

        if ruhe.still() and not wach and z == "ruhe":
            a = np.zeros((N, N, 3), np.uint8)
        elif z == "denkt":
            a = zeichnen(blick=-3.5 if int(jetzt / 0.8) % 2 else 3.5, hoch=-4, denkt=True,
                         farbe=GELB, hell=HELL_AKTIV)
        else:
            a = zeichnen(blick=blick if jetzt < blick_bis and z == "ruhe" else 0.0,
                         blinzeln=jetzt < blinzeln_bis, mund=mund_weich,
                         hell=HELL_RUHE if z == "ruhe" else HELL_AKTIV)
        _bild = a.tobytes()
        if ip:
            seq = seq % 15 + 1
            try:
                _an_matrix(ip, a, seq, seite)
            except OSError:
                pass
        time.sleep(1 / FPS)


def starten() -> None:
    threading.Thread(target=_schleife, name="gesicht", daemon=True).start()
