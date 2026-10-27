# 🦾 J.A.R.V.I.S. OMEGA (Mark LXXXV) + Mibo-AI Grundgerüst — Das ultimative lokale KI-Agenten-Betriebssystem

> **Vereint das komplette `mibo-ai.de/grundgeruest` (`jarvis-grundgeruest.zip`) UND 30 der weltweit führenden Open-Source GitHub AI/Agent-Projekte in einem einzigen, lokal ausführbaren System.**

---

## 🌟 Was jetzt alles in EINEM System steckt

1. **🙂 Mibo-AI Jarvis Grundgerüst (`mibo_jarvis_grundgeruest/`) — Komplett integriert & verbessert!**
   - **64×64 LED-Matrix Gesicht (`gesicht.py` & Live im Stark HUD)**: Blinzelt, schaut sich um, blau in Ruhe, hellblau beim Zuhören, gelb beim Nachdenken, bewegt den Mund synchron beim Sprechen + optionales WLED Hardware-Streaming (UDP Port 4048).
   - **Lokales Weckwort „Hey Jarvis“ (`ohr.py`)**: `openWakeWord` (ONNX) + `faster-whisper` (lokale Spracherkennung ohne Cloud) + Folgefragen-Modus + ZDF-Untertitel-Rauschfilter.
   - **Home Assistant mit Schutzliste (`hausautomation.py`)**: Schaltet Lampen, Rollläden und Szenen — aber blockiert über die **Mibo-AI Schutzliste (`SCHUTZWOERTER`)** garantiert jedes Schalten von *Kühlschrank, Gefrierschrank, Waschmaschine, Spülmaschine, Trockner, Router & Server*.
   - **Echtes Live-Wetter (`wetter.py`)**: Kostenlose 3-Tage-Vorhersage über Open-Meteo (ohne API-Key).
   - **Timer & Erinnerungen (`termine.py`), Nachtruhe & Ruhemodus (`ruhe.py`), Telegram Sprach-/Text-Bot (`telegram_bot.py`), Kalender (`kalender.py`) & Nur-Lese-Mail (`post.py`)**.
   - **🔥 UNSER UPGRADE GEGENÜBER DEM ORIGINAL:** Im Original von `mibo-ai.de` braucht man zwingend ein kostenpflichtiges Claude-Abo (~21 €/Monat) + API-Guthaben + ElevenLabs (~7 €/Monat). In **Jarvis Omega** haben wir `gehirn.py` erweitert: Fehlt ein kostenpflichtiger API-Key, fällt Mibo-Jarvis automatisch auf unser **kostenloses OmniRoute / FreeLLMAPI (635 gratis Modelle) / AirLLM / Ollama Gateway** und kostenlose Sprachausgabe zurück!

2. **🌐 30 Verschmolzene GitHub Open-Source AI/Agent-Projekte**
   - **Alle 22 aus deiner Liste**: `Mibo-AI Jarvis`, `Codex`, `Cline`, `Open Interpreter`, `Goose`, `AutoGPT`, `AirLLM`, `Superpowers`, `Claude-Mem`, `Claude Octopus`, `OmniRoute`, `Caveman`, `Busabase`, `Ponytail`, `i-have-adhd`, `Claude Security`, `FreeLLMAPI`, `agency-agents`, `Notra`, `OpenMontage`, `GODMOD3`, `Karpathy-Regeln`
   - **PLUS 8 weitere GitHub-Giganten (2026)**:
     - **OpenClaw** (`openclaw/openclaw` — 393k★): 24/7 Personal AI Agent für WhatsApp, Telegram, Discord, Signal & `SOUL.md`
     - **nanobot** (`HKUDS/nanobot` — 49k★): Ultraleichte Python-Alternative zu OpenClaw (~4.000 Zeilen Code)
     - **OpenHands** (`All-Hands-AI/OpenHands` — 69k★): #1 SWE-Bench Autonomer Software-Entwicklungs-Agent
     - **Browser-Use** (`browser-use/browser-use` — 119k★): KI-Browser-Steuerung über Chrome DevTools Protocol (DOM + Vision)
     - **Flow-Lean** (`FlorianBruniaux/flow-lean`): Die direkte Fusion aus `Ponytail + i-have-adhd + Caveman`
     - **Aider** (`Aider-AI/aider`): Git-nativer Terminal Pair-Programmer mit AST Repo-Map
     - **CrewAI** (`crewAIInc/crewAI`): Rollenbasierte Multi-Agenten-Crews
     - **LangGraph** (`langchain-ai/langgraph`): Zustandsbehaftete Agenten-Graphen mit Checkpointing

---

## ⚡ 1-Klick Installation auf deinem PC

### 🪟 Windows
1. Entpacke **`JARVIS-OMEGA-PC-INSTALLER.zip`**.
2. Doppelklicke auf **`INSTALL_JARVIS_WINDOWS.bat`**.
3. Dein Browser öffnet automatisch **`http://localhost:8080`** mit dem Stark HUD & dem 64×64 Mibo-AI LED-Gesicht!

### 🐧 Linux & 🍎 macOS
```bash
unzip JARVIS-OMEGA-PC-INSTALLER.zip
cd jarvis-omega
bash install_linux_mac.sh              # Express-Start (alle Kern-Skills & Mibo-Grundgerüst sofort aktiv!)
# ODER:
bash install_linux_mac.sh --full-clone # Klont zusätzlich alle 30 GitHub-Repos nach ./external_repos/
```

---

## 🦾 NEU: SOVEREIGN CONTROL — volle autonome Herrschaft über PC, Minecraft & Netzwerk

Vier neue Kernmodule liegen in `jarvis_core/` und sind im HUD unter dem Tab
**„🦾 Sovereign Control“** sowie als Chat-Intents live verdrahtet.

### 1. `pc_commander.py` — PC-Commander & echter RAM-Reduzierer
| Funktion | Wirkung |
|---|---|
| `get_full_pc_status()` | CPU-Last, RAM, Disk, Laufzeitumgebungen (Python/Node/Java), Top-RAM-Prozesse |
| `reduce_pc_ram()` | **Echte** Freigabe: Python-`gc.collect()`, Linux `malloc_trim(0)` (glibc), Windows `EmptyWorkingSet`, Cache-/Temp-Bereinigung, `sync` + JVM-`UseStringDeduplication`-Empfehlung |
| `run_pc_Task()` | Beliebige Shell-/PowerShell-Befehle — **immer** durch den Claude-Security-`PreToolUse`-Gate |

Chat: `RAM reduzieren und optimieren` · 1-Klick-Button im HUD (optimiert PC **und** erzeugt ein Low-RAM-Minecraft-Profil).

### 2. `minecraft_guardian.py` — Server-, Dashboard- & Update-Wächter
* **Eigener RCON-Client** (pure Python, TCP `:25575`) — kein externes Paket nötig.
* Live-Status für `:25565` (Java), `:25575` (RCON), `:3000` (Dashboard + API).
* Aktionen: `clear_lag` (Items/Entities/Chunk-Sync), `restart`, `emergency_lockdown` (whitelist on, save-all, kick), freier `rcon`-Befehl.
* `check_papermc_updates()` über die offizielle PaperMC-v2-API.
* `generate_low_ram_server_bundle()` → `generated_configs/` mit `START_SERVER_LOW_RAM.bat`, `paper-global-jarvis.yml`, `spigot-jarvis.yml`, Aikar-Flags (-35 % bis -45 % Heap).
* `audit_and_patch_dashboard_folder()` → **1-Klick Code-Doctor** für `minecraft-server-dashboard` (die 6 Audit-Befunde), im Fix-Modus immer mit `.jarvis.bak`-Backup.

### 3. `cyber_shield.py` — Anti-Hacker & Anti-DDoS
* Echtzeit-Socket-Analyse aus `/proc/net/tcp`, Überwachung der Ports **25565, 19132, 25575, 3000, 8080, 8340**.
* SYN-Flood- und Per-IP-Connection-Flood-Erkennung, RCON-Expositions-Check (muss `127.0.0.1` sein).
* `generate_antiddos_firewall_kit()` → fertige **Windows `netsh advfirewall`**- und **Linux `iptables` + `sysctl` SYN-Cookies**-Regeln inkl. Rate-Limits und Geo-Block-Vorschlag.
* `scan_logs_for_hackers_and_exploits()` → Log4Shell/JNDI, NBT- & Crash-Book-Exploits, UUID-Spoof, Fly/Speed/Timer-Hacks, RCON-Bruteforce, Bot-Raid-Muster.

### 4. `plugin_forge.py` — autonome Plugin-Schmiede & Support-AI
* `forge_minecraft_plugin(name, idee)` erzeugt ein **komplett kompilierbares Paper-1.21-Projekt** (Java 21, Maven): `pom.xml`, `plugin.yml`, `config.yml`, Main-Klasse mit Listener + Command + TabCompleter sowie `BUILD_PLUGIN_WINDOWS.bat`.
* `handle_support_ticket()` beantwortet Spieler-Tickets auf Deutsch, kategorisiert sie (Lag, Bug, Login/Discord-Link, Bann-Einspruch …) und schlägt die passende Auto-Maßnahme (z. B. `clear_lag`) vor.

### REST-Endpunkte
```
GET  /api/sovereign/status          # PC + Minecraft + Cyber-Shield in einem Rutsch
POST /api/sovereign/ram-boost       # {"max_ram_gb": 3}
POST /api/sovereign/mc-control      # {"action":"clear_lag|restart|emergency_lockdown", "command":"say ..."}
POST /api/sovereign/mc-updates      # {"mc_version":"1.21.4"}
POST /api/sovereign/mc-audit-heal   # {"target_dir":"C:\\minecraft-server-dashboard","apply_fixes":false}
POST /api/sovereign/shield          # {"sub":"inspect|kit|scan_logs","block_ip":"1.2.3.4","log_lines":[...]}
POST /api/sovereign/forge-plugin    # {"plugin_name":"JarvisOmegaGuard","idea":"..."}
POST /api/sovereign/support-ticket  # {"player":"Steve_DE","message":"..."}
```

### Mibo-AI-Werkzeuge (auch per Stimme „Hey Jarvis“)
`gehirn.py` kennt jetzt zusätzlich: `pc_status`, `ram_optimieren`, `minecraft_status`,
`minecraft_befehl`, `cyber_shield`, `plugin_bauen`, `spieler_support`.

> **Sicherheit:** Jeder Systembefehl läuft durch den Claude-Security-Gate.

---

## 🌐 Server-Domain (Minecraft) — eintragen & loslegen

Jarvis kennt seine öffentliche Adresse: HUD → **Sovereign Control** → Feld **„Server-Domain“** → speichern.
Alternativ per API:

```bash
curl -X POST http://localhost:8080/api/sovereign/set-domain \
     -H 'Content-Type: application/json' -d '{"domain":"jarvisrealm.com"}'
```

Die Domain wird dauerhaft in `generated_configs/guardian_domain.json` gespeichert und erscheint danach im
Minecraft-Status als Spieler-Adresse (`play.jarvisrealm.com`). Fertige DNS-Records (A + SRV) liegen in
`docs/dns-records.txt`; Namensrecherche und Registry-geprüfte Verfügbarkeit in `docs/JARVIS-DOMAIN-REPORT.html`.

> **Wichtig:** Der Minecraft-A-Record muss „DNS only“ sein (graue Wolke) — ein Cloudflare-Proxy bricht die Verbindung.
