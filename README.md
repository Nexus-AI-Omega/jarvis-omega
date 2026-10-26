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
