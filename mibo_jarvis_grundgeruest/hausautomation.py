"""Home Assistant: Geraete finden, schalten, Werte abfragen.

Zugang: config.json "home_assistant_url" (z.B. http://homeassistant.local:8123)
und "home_assistant_token" (in HA: Profil -> Sicherheit -> Langlebiges
Zugriffstoken).

SCHUTZLISTE: Geraete, die nie per Sprache geschaltet werden duerfen — ein
falsch verstandenes "aus" am Kuehlschrank waere teuer. Dazu gehoeren alle
Entitaeten aus config.json "schutzliste" und alles, dessen Name eines der
SCHUTZWOERTER enthaelt. Abfragen ("ist die Waschmaschine fertig?") gehen.
"""

import httpx

import konfig

SCHUTZWOERTER = (
    # Geraete, die durchlaufen muessen (Home Assistant schreibt Umlaute in IDs als u/o/a)
    "kühlschrank", "kuehlschrank", "kuhlschrank", "gefrier", "waschmaschine", "spülmaschine",
    "spuelmaschine", "spulmaschine", "geschirrspüler", "geschirrspuler", "trockner",
    # Netzwerk und Technik: wer das abschaltet, schaltet Jarvis selbst ab
    "router", "fritzbox", "fritz_box", "fritz!box", "repeater", "wlan", "wi_fi", "wi-fi",
    "internet_access", "internetzugang", "server", "homeassistant", "home assistant", "home_assistant")

SCHALTBAR = ("light", "switch", "fan", "cover", "media_player", "climate", "scene", "script",
             "input_boolean", "lock", "vacuum")


def aktiv() -> bool:
    return bool(konfig.get("home_assistant_url") and konfig.get("home_assistant_token"))


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=konfig.get("home_assistant_url").rstrip("/"), timeout=15,
                             headers={"Authorization": f"Bearer {konfig.get('home_assistant_token')}"})


def _geschuetzt(zustand: dict) -> bool:
    eid = zustand["entity_id"]
    name = (zustand.get("attributes", {}).get("friendly_name") or "").lower()
    return eid in (konfig.get("schutzliste") or []) or any(w in name or w in eid for w in SCHUTZWOERTER)


async def _zustaende() -> list[dict]:
    async with _client() as c:
        r = await c.get("/api/states")
        r.raise_for_status()
        return r.json()


def _kurz(z: dict) -> str:
    a = z.get("attributes", {})
    einheit = a.get("unit_of_measurement", "")
    zusatz = f", Helligkeit {round(a['brightness'] / 2.55)} %" if a.get("brightness") else ""
    return f"{a.get('friendly_name', z['entity_id'])} [{z['entity_id']}]: {z['state']}{(' ' + einheit) if einheit else ''}{zusatz}"


async def suchen(stichwort: str) -> str:
    """Geraete/Sensoren, deren Name oder ID das Stichwort enthaelt (hoechstens 25)."""
    w = stichwort.lower().strip()
    treffer = [z for z in await _zustaende()
               if w in z["entity_id"].lower() or w in (z.get("attributes", {}).get("friendly_name") or "").lower()]
    if not treffer:
        return f"Nichts zu '{stichwort}' gefunden."
    return "\n".join(_kurz(z) for z in treffer[:25]) + (f"\n… und {len(treffer) - 25} weitere" if len(treffer) > 25 else "")


async def schalten(entity_id: str, aktion: str, helligkeit: int | None = None) -> str:
    """aktion: an, aus oder umschalten. helligkeit (0-100) nur fuer Lampen."""
    alle = {z["entity_id"]: z for z in await _zustaende()}
    z = alle.get(entity_id)
    if not z:
        return f"'{entity_id}' gibt es nicht. Erst mit ha_suchen die richtige ID finden."
    if _geschuetzt(z):
        return f"'{z['attributes'].get('friendly_name', entity_id)}' steht auf der Schutzliste und wird nicht geschaltet."
    bereich = entity_id.split(".")[0]
    if bereich not in SCHALTBAR:
        return f"'{entity_id}' ist ein Sensor und laesst sich nicht schalten."
    dienst = {"an": "turn_on", "aus": "turn_off", "umschalten": "toggle"}.get(aktion)
    if bereich in ("scene", "script"):
        dienst = "turn_on"
    if bereich == "cover":
        dienst = {"turn_on": "open_cover", "turn_off": "close_cover", "toggle": "toggle"}[dienst]
    if not dienst:
        return "Aktion bitte: an, aus oder umschalten."
    daten = {"entity_id": entity_id}
    if helligkeit is not None and bereich == "light" and dienst == "turn_on":
        daten["brightness_pct"] = max(1, min(100, int(helligkeit)))
    async with _client() as c:
        r = await c.post(f"/api/services/{bereich}/{dienst}", json=daten)
    if r.status_code >= 400:
        return f"Home Assistant meldet Fehler {r.status_code}: {r.text[:150]}"
    return f"Erledigt: {z['attributes'].get('friendly_name', entity_id)} -> {aktion}."
