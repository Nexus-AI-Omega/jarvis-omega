"""Wetter von Open-Meteo (kostenlos, ohne Zugangsschluessel)."""

import httpx

import konfig

_ort: tuple[float, float, str] | None = None

WETTERCODES = {
    0: "klar", 1: "ueberwiegend klar", 2: "teils bewoelkt", 3: "bedeckt", 45: "Nebel", 48: "Reifnebel",
    51: "leichter Nieselregen", 53: "Nieselregen", 55: "starker Nieselregen", 61: "leichter Regen",
    63: "Regen", 65: "starker Regen", 66: "gefrierender Regen", 67: "starker gefrierender Regen",
    71: "leichter Schneefall", 73: "Schneefall", 75: "starker Schneefall", 77: "Schneegriesel",
    80: "leichte Regenschauer", 81: "Regenschauer", 82: "heftige Regenschauer", 85: "Schneeschauer",
    86: "starke Schneeschauer", 95: "Gewitter", 96: "Gewitter mit Hagel", 99: "schweres Gewitter mit Hagel",
}


async def _koordinaten(ort: str) -> tuple[float, float, str]:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": ort, "count": 1, "language": "de"})
    treffer = (r.json().get("results") or [None])[0]
    if not treffer:
        raise ValueError(f"Ort '{ort}' nicht gefunden")
    return treffer["latitude"], treffer["longitude"], treffer["name"]


async def wetter(ort: str = "") -> str:
    """Aktuelles Wetter und die naechsten drei Tage."""
    global _ort
    if ort:
        lat, lon, name = await _koordinaten(ort)
    else:
        if _ort is None:
            _ort = await _koordinaten(konfig.get("stadt") or "Berlin")
        lat, lon, name = _ort
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 3,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        })
    d = r.json()
    j = d["current"]
    zeilen = [f"{name} jetzt: {j['temperature_2m']:.0f} °C (gefuehlt {j['apparent_temperature']:.0f} °C), "
              f"{WETTERCODES.get(j['weather_code'], 'unbekannt')}, Wind {j['wind_speed_10m']:.0f} km/h."]
    t = d["daily"]
    for i, tag in enumerate(("Heute", "Morgen", "Uebermorgen")):
        zeilen.append(f"{tag}: {t['temperature_2m_min'][i]:.0f} bis {t['temperature_2m_max'][i]:.0f} °C, "
                      f"{WETTERCODES.get(t['weather_code'][i], 'unbekannt')}, "
                      f"Regenrisiko {t['precipitation_probability_max'][i]} %.")
    return "\n".join(zeilen)
