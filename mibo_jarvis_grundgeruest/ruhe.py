"""Nachtruhe und Ruhemodus.

Nachtruhe (config.json "nachtruhe", z.B. "23:00-07:00"): Jarvis meldet sich
in der Zeit nicht von selbst zu Wort, Erinnerungen kommen dann nur per
Telegram, das Gesicht ist dunkel. Angesprochen antwortet er natuerlich.

Ruhemodus ("Jarvis, Ruhemodus an"): wie Nachtruhe, aber rund um die Uhr,
bis man ihn wieder ausschaltet. Er bleibt ueber einen Neustart erhalten.
"""

import time

import konfig


def _nachtruhe_jetzt() -> bool:
    zeit = konfig.get("nachtruhe") or ""
    try:
        von, bis = ((int(h) * 60 + int(m)) for h, m in (t.split(":") for t in zeit.split("-")))
    except ValueError:
        return False
    t = time.localtime()
    jetzt = t.tm_hour * 60 + t.tm_min
    return von <= jetzt < bis if von < bis else (jetzt >= von or jetzt < bis)


_an: bool | None = None     # zwischengespeichert — das Gesicht fragt 20-mal pro Sekunde


def ruhemodus() -> bool:
    global _an
    if _an is None:
        _an = bool(konfig.laden("ruhemodus.json", {}).get("an"))
    return _an


def setze_ruhemodus(an: bool) -> None:
    global _an
    _an = bool(an)
    konfig.speichern("ruhemodus.json", {"an": _an})


def still() -> bool:
    """True, wenn Jarvis gerade nicht von selbst sprechen soll."""
    return ruhemodus() or _nachtruhe_jetzt()
