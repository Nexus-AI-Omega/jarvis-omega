"""Termine aus einem Kalender lesen (nur lesen).

config.json "kalender_ics_url": die geheime iCal-Adresse des Kalenders —
Google Kalender: Einstellungen -> Kalender -> "Privatadresse im iCal-Format";
iCloud: Kalender freigeben -> "Oeffentlicher Kalender" (webcal:// geht auch).
"""

from datetime import date, datetime, timedelta

import httpx

import konfig


def aktiv() -> bool:
    return bool(konfig.get("kalender_ics_url"))


async def termine(tage: int = 7) -> str:
    """Termine von heute bis in `tage` Tagen."""
    import icalendar
    import recurring_ical_events
    url = konfig.get("kalender_ics_url").replace("webcal://", "https://")
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        r = await c.get(url)
        r.raise_for_status()
    cal = icalendar.Calendar.from_ical(r.content)
    heute = date.today()
    ereignisse = recurring_ical_events.of(cal).between(heute, heute + timedelta(days=max(1, tage)))
    zeilen = []
    for e in sorted(ereignisse, key=lambda e: str(e.get("DTSTART").dt)):
        start = e.get("DTSTART").dt
        if isinstance(start, datetime):
            wann = start.astimezone().strftime("%a %d.%m. %H:%M")
        else:
            wann = start.strftime("%a %d.%m. (ganztägig)")
        ort = f" – {e.get('LOCATION')}" if e.get("LOCATION") else ""
        zeilen.append(f"{wann}: {e.get('SUMMARY', '(ohne Titel)')}{ort}")
    return "\n".join(zeilen) or f"Keine Termine in den naechsten {tage} Tagen."
