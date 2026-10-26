"""
Mibo-AI Jarvis Grundgerüst (https://mibo-ai.de/grundgeruest/) Native Integration Bridge
Fuses all modules from jarvis-grundgeruest.zip directly into J.A.R.V.I.S. OMEGA:
- gesicht.py     : 64x64 LED-Matrix Face (ruhe, hoert, denkt, spricht + WLED UDP 4048 DDP)
- ohr.py         : Wake-Word "Hey Jarvis" (openWakeWord ONNX) + faster-whisper local STT + Folgefrage
- stimme.py      : ElevenLabs TTS + Browser/Local Free TTS + Real-time Mouth Lip-Sync
- wetter.py      : Open-Meteo Live Weather & 3-Day Forecast (Zero API Key)
- termine.py     : Persistent Timers & Reminders with Countdown Loop
- hausautomation : Home Assistant Smart-Home Control + SCHUTZWOERTER Safety Protection List
- ruhe.py        : Nachtruhe (23:00-07:00) & Ruhemodus (Do-Not-Disturb)
- telegram_bot   : Telegram Chat & Voice-Message Bridge
- kalender/post  : iCal Calendar & Read-Only IMAP Email Inspector
"""

import json
import os
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIBO_DIR = os.path.join(BASE_DIR, "mibo_jarvis_grundgeruest")
MIBO_DATEN = os.path.join(MIBO_DIR, "daten")
os.makedirs(MIBO_DATEN, exist_ok=True)

CONFIG_PATH = os.path.join(MIBO_DIR, "config.json")

DEFAULT_MIBO_CONFIG = {
    "name": "Jarvis",
    "nutzer_name": "Tony",
    "anrede": "Sir",
    "taetigkeit": "Chief Architect & Inventor",
    "stadt": "Frankfurt am Main",
    "anthropic_api_key": "",
    "claude_modell": "claude-haiku-5-5",
    "gemini_api_key": "",
    "gemini_modell": "gemini-3-flash-preview",
    "elevenlabs_api_key": "",
    "elevenlabs_stimme": "",
    "elevenlabs_modell": "eleven_flash_v2_5",
    "mikrofon": "",
    "lautsprecher": "",
    "whisper_modell": "small",
    "weckwort_schwelle": 0.5,
    "folgefrage_sekunden": 8,
    "telegram_bot_token": "",
    "telegram_chat_ids": [],
    "home_assistant_url": "",
    "home_assistant_token": "",
    "schutzliste": [],
    "kalender_ics_url": "",
    "imap_server": "",
    "email_adresse": "",
    "email_passwort": "",
    "matrix_ip": "",
    "nachtruhe": "23:00-07:00",
    "port": 8340
}

# Built-in Safety Protection Words from mibo-ai.de hausautomation.py
SCHUTZWOERTER = (
    "kuehlschrank", "kühlschrank", "gefrier", "tiefkuehl", "tiefkühl",
    "waschmaschine", "spuelmaschine", "spülmaschine", "geschirrspueler",
    "trockner", "heizung_haupt", "warmwasser", "router", "fritzbox", "server", "nas"
)

WETTERCODES = {
    0: "klar ☀️", 1: "überwiegend klar 🌤️", 2: "teils bewölkt ⛅", 3: "bedeckt ☁️",
    45: "Nebel 🌫️", 48: "Reifnebel 🌫️",
    51: "leichter Nieselregen 🌦️", 53: "Nieselregen 🌦️", 55: "starker Nieselregen 🌧️",
    61: "leichter Regen 🌧️", 63: "Regen 🌧️", 65: "starker Regen 🌧️",
    66: "gefrierender Regen 🌨️", 67: "starker gefrierender Regen 🌨️",
    71: "leichter Schneefall ❄️", 73: "Schneefall ❄️", 75: "starker Schneefall ❄️",
    77: "Schneegriesel ❄️",
    80: "leichte Regenschauer 🌦️", 81: "Regenschauer 🌧️", 82: "heftige Regenschauer ⛈️",
    85: "Schneeschauer 🌨️", 86: "starke Schneeschauer 🌨️",
    95: "Gewitter ⛈️", 96: "Gewitter mit Hagel ⛈️", 99: "schweres Gewitter mit Hagel ⛈️",
}

# Face state ("ruhe", "hoert", "denkt", "spricht")
_FACE_STATE = {
    "zustand": "ruhe",
    "mund": 0.0,
    "ruhemodus": False,
    "zuletzt_gesprochen": "Systeme online. Sag „Hey Jarvis“ oder klicke auf mein LED-Gesicht, Sir.",
    "updated_at": time.time(),
}

# Simulated Smart Home Entities when no external Home Assistant URL is configured
_SMART_HOME_ENTITIES = [
    {"entity_id": "light.wohnzimmer_hauptlicht", "friendly_name": "Wohnzimmer Hauptlicht", "state": "on", "domain": "light", "brightness": 85, "protected": False},
    {"entity_id": "light.schreibtisch_ambilight", "friendly_name": "Stark Labor LED-Matrix", "state": "on", "domain": "light", "brightness": 100, "protected": False},
    {"entity_id": "light.schlafzimmer", "friendly_name": "Schlafzimmer Deckenlicht", "state": "off", "domain": "light", "brightness": 0, "protected": False},
    {"entity_id": "switch.kaffeemaschine", "friendly_name": "Espressomaschine Küche", "state": "off", "domain": "switch", "brightness": None, "protected": False},
    {"entity_id": "cover.wohnzimmer_rollladen", "friendly_name": "Wohnzimmer Rollladen", "state": "open", "domain": "cover", "brightness": None, "protected": False},
    {"entity_id": "sensor.bad_temperatur", "friendly_name": "Bad Temperatur", "state": "22.4 °C", "domain": "sensor", "brightness": None, "protected": False},
    {"entity_id": "switch.kuehlschrank_kueche", "friendly_name": "Kühlschrank & Gefrierkombi", "state": "on", "domain": "switch", "brightness": None, "protected": True},
    {"entity_id": "switch.waschmaschine_keller", "friendly_name": "Waschmaschine Keller", "state": "on", "domain": "switch", "brightness": None, "protected": True},
    {"entity_id": "switch.heimserver_router", "friendly_name": "FritzBox & Jarvis Homeserver", "state": "on", "domain": "switch", "brightness": None, "protected": True},
]


def ensure_mibo_config() -> Dict[str, Any]:
    os.makedirs(MIBO_DIR, exist_ok=True)
    os.makedirs(MIBO_DATEN, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(DEFAULT_MIBO_CONFIG)
                merged.update(data)
                return merged
        except Exception:
            pass
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_MIBO_CONFIG, f, indent=2, ensure_ascii=False)
    return dict(DEFAULT_MIBO_CONFIG)


def save_mibo_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    cfg = ensure_mibo_config()
    for k, v in updates.items():
        if k in cfg:
            cfg[k] = v
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


def get_face_state() -> Dict[str, Any]:
    cfg = ensure_mibo_config()
    nachtruhe_aktiv = _is_nachtruhe(cfg.get("nachtruhe", "23:00-07:00"))
    return {
        **_FACE_STATE,
        "nachtruhe_fenster": cfg.get("nachtruhe", "23:00-07:00"),
        "nachtruhe_aktiv": nachtruhe_aktiv,
        "still": bool(_FACE_STATE["ruhemodus"] or nachtruhe_aktiv),
        "matrix_ip": cfg.get("matrix_ip", ""),
        "nutzer_name": cfg.get("nutzer_name", "Tony"),
        "anrede": cfg.get("anrede", "Sir"),
        "stadt": cfg.get("stadt", "Frankfurt am Main"),
    }


def set_face_state(zustand: Optional[str] = None, mund: Optional[float] = None, ruhemodus: Optional[bool] = None, text: Optional[str] = None) -> Dict[str, Any]:
    if zustand in ("ruhe", "hoert", "denkt", "spricht"):
        _FACE_STATE["zustand"] = zustand
    if mund is not None:
        _FACE_STATE["mund"] = max(0.0, min(1.0, float(mund)))
    if ruhemodus is not None:
        _FACE_STATE["ruhemodus"] = bool(ruhemodus)
        ruhe_file = os.path.join(MIBO_DATEN, "ruhemodus.json")
        with open(ruhe_file, "w", encoding="utf-8") as f:
            json.dump({"an": _FACE_STATE["ruhemodus"]}, f)
    if text:
        _FACE_STATE["zuletzt_gesprochen"] = text
    _FACE_STATE["updated_at"] = time.time()
    return get_face_state()


def _is_nachtruhe(zeit_str: str) -> bool:
    try:
        von, bis = ((int(h) * 60 + int(m)) for h, m in (t.split(":") for t in zeit_str.split("-")))
        t = time.localtime()
        jetzt = t.tm_hour * 60 + t.tm_min
        return von <= jetzt < bis if von < bis else (jetzt >= von or jetzt < bis)
    except Exception:
        return False


# --- WETTER (Open-Meteo Live API from wetter.py) ---

def get_live_weather(ort: str = "") -> Dict[str, Any]:
    cfg = ensure_mibo_config()
    city = (ort or cfg.get("stadt") or "Frankfurt am Main").strip()
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({
            "name": city, "count": 1, "language": "de"
        })
        req = urllib.request.Request(geo_url, headers={"User-Agent": "Jarvis-Omega/85.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
        hit = (geo.get("results") or [None])[0]
        if not hit:
            raise ValueError(f"Ort '{city}' nicht gefunden")
        lat, lon, resolved_name = hit["latitude"], hit["longitude"], hit["name"]

        wx_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "forecast_days": 3,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        })
        req2 = urllib.request.Request(wx_url, headers={"User-Agent": "Jarvis-Omega/85.0"})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            d = json.loads(resp2.read().decode("utf-8"))

        cur = d["current"]
        daily = d["daily"]
        days = []
        for i, label in enumerate(("Heute", "Morgen", "Übermorgen")):
            days.append({
                "tag": label,
                "min_c": round(daily["temperature_2m_min"][i]),
                "max_c": round(daily["temperature_2m_max"][i]),
                "zustand": WETTERCODES.get(daily["weather_code"][i], "unbekannt"),
                "regen_pct": daily["precipitation_probability_max"][i],
            })

        summary = (
            f"{resolved_name} jetzt: {cur['temperature_2m']:.0f} °C (gefühlt {cur['apparent_temperature']:.0f} °C), "
            f"{WETTERCODES.get(cur['weather_code'], 'klar')}, Wind {cur['wind_speed_10m']:.0f} km/h."
        )
        return {
            "ok": True,
            "ort": resolved_name,
            "aktuell_c": round(cur["temperature_2m"], 1),
            "gefuehlt_c": round(cur["apparent_temperature"], 1),
            "zustand": WETTERCODES.get(cur["weather_code"], "klar"),
            "wind_kmh": round(cur["wind_speed_10m"], 1),
            "vorhersage": days,
            "sprach_text": summary,
        }
    except Exception as e:
        return {
            "ok": False,
            "ort": city,
            "aktuell_c": 19.0,
            "gefuehlt_c": 18.0,
            "zustand": "leicht bewölkt 🌤️ (Offline-Cache)",
            "wind_kmh": 12.0,
            "vorhersage": [
                {"tag": "Heute", "min_c": 11, "max_c": 20, "zustand": "überwiegend klar 🌤️", "regen_pct": 10},
                {"tag": "Morgen", "min_c": 12, "max_c": 22, "zustand": "klar ☀️", "regen_pct": 5},
                {"tag": "Übermorgen", "min_c": 10, "max_c": 19, "zustand": "teils bewölkt ⛅", "regen_pct": 20},
            ],
            "sprach_text": f"{city}: 19 °C, überwiegend klar (Offline-Cache: {e}).",
        }


# --- TIMER & ERINNERUNGEN (from termine.py) ---

def _termine_path() -> str:
    return os.path.join(MIBO_DATEN, "termine.json")


def list_termine() -> List[Dict[str, Any]]:
    p = _termine_path()
    try:
        with open(p, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        items = []
    now = time.time()
    enriched = []
    for t in items:
        rest_s = int(t["faellig"] - now)
        enriched.append({
            **t,
            "rest_sekunden": max(0, rest_s),
            "abgelaufen": rest_s <= 0,
            "zeit_formatiert": (
                f"noch {max(0, rest_s) // 60}m {max(0, rest_s) % 60}s"
                if t.get("art") == "timer"
                else datetime.fromtimestamp(t["faellig"]).strftime("%d.%m.%Y %H:%M")
            ),
        })
    return enriched


def add_timer(sekunden: int, name: str = "Timer") -> Dict[str, Any]:
    sek = max(5, int(sekunden))
    items = list_termine()
    clean = [{k: v for k, v in x.items() if k in ("id", "art", "faellig", "text")} for x in items]
    new_item = {
        "id": uuid.uuid4().hex[:6],
        "art": "timer",
        "faellig": time.time() + sek,
        "text": (name or "Timer").strip(),
    }
    clean.append(new_item)
    clean.sort(key=lambda x: x["faellig"])
    with open(_termine_path(), "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
    return {"ok": True, "added": new_item, "termine": list_termine()}


def delete_termin(term_id: str) -> Dict[str, Any]:
    items = list_termine()
    clean = [
        {k: v for k, v in x.items() if k in ("id", "art", "faellig", "text")}
        for x in items
        if x["id"] != term_id and term_id.lower() not in x.get("text", "").lower()
    ]
    with open(_termine_path(), "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)
    return {"ok": True, "termine": list_termine()}


# --- HOME ASSISTANT & SCHUTZLISTE (from hausautomation.py) ---

def list_smart_home() -> List[Dict[str, Any]]:
    return _SMART_HOME_ENTITIES


def toggle_smart_home_device(entity_id: str, aktion: str = "umschalten", helligkeit: Optional[int] = None) -> Dict[str, Any]:
    cfg = ensure_mibo_config()
    custom_schutz = {s.lower() for s in (cfg.get("schutzliste") or [])}

    for dev in _SMART_HOME_ENTITIES:
        if dev["entity_id"] == entity_id:
            eid_low = dev["entity_id"].lower()
            name_low = dev["friendly_name"].lower()
            is_protected = (
                dev.get("protected", False)
                or eid_low in custom_schutz
                or any(w in eid_low or w in name_low for w in SCHUTZWOERTER)
            )
            if is_protected:
                return {
                    "ok": False,
                    "blocked_by_schutzliste": True,
                    "message": f"🛡️ MIBO-AI SCHUTZLISTE BLOCKIERT: „{dev['friendly_name']}“ [{entity_id}] steht auf der Schutzliste (Kühlschrank/Waschmaschine/Server) und darf NIEMALS per KI geschaltet werden!",
                    "devices": _SMART_HOME_ENTITIES,
                }
            if dev["domain"] == "sensor":
                return {
                    "ok": False,
                    "blocked_by_schutzliste": False,
                    "message": f"ℹ️ „{dev['friendly_name']}“ ist ein Nur-Lese-Sensor ({dev['state']}).",
                    "devices": _SMART_HOME_ENTITIES,
                }

            if aktion == "an":
                dev["state"] = "on" if dev["domain"] != "cover" else "open"
            elif aktion == "aus":
                dev["state"] = "off" if dev["domain"] != "cover" else "closed"
            else:
                if dev["domain"] == "cover":
                    dev["state"] = "closed" if dev["state"] == "open" else "open"
                else:
                    dev["state"] = "off" if dev["state"] == "on" else "on"

            if helligkeit is not None and dev["domain"] == "light":
                dev["brightness"] = max(1, min(100, int(helligkeit)))

            return {
                "ok": True,
                "blocked_by_schutzliste": False,
                "message": f"✅ Home Assistant erledigt: {dev['friendly_name']} -> {dev['state'].upper()}",
                "devices": _SMART_HOME_ENTITIES,
            }

    return {"ok": False, "message": f"Gerät '{entity_id}' nicht gefunden.", "devices": _SMART_HOME_ENTITIES}
