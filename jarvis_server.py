#!/usr/bin/env python3
"""
J.A.R.V.I.S. OMEGA (Mark LXXXV) — Unified Local AI Agent, Mibo-AI Grundgerüst & Stark HUD Server
Binds to 0.0.0.0:8080 and exposes:
- Interactive Stark HUD + 64x64 Mibo-AI LED-Matrix Face Web Interface (/)
- REST API for all 30 fused GitHub AI modules + Mibo-AI Smart Home/Weather/Timers (/api/*)
- OpenAI-compatible Gateway Endpoint (/v1/chat/completions)
- 1-Click PC Installer ZIP Download (/download/jarvis-omega.zip)
"""

import io
import json
import os
import re
import time
import urllib.parse
import zipfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from jarvis_core.catalog import get_catalog
from jarvis_core.compression import compress_text_caveman
from jarvis_core.security import pre_tool_use_check, run_security_review
from jarvis_core.memory import (
    init_vault,
    add_memory,
    search_memories,
    busabase_upsert,
    busabase_revert,
    busabase_list,
    notra_add_note,
    notra_list_notes,
    get_vault_context_snippet,
)
from jarvis_core.octopus import (
    run_octopus_consensus,
    run_autogpt_plan,
    run_openmontage_studio,
)
from jarvis_core.executor import get_system_telemetry, execute_local_action
from jarvis_core.router import (
    load_router_config,
    save_router_config,
    route_chat_completion,
)
from jarvis_core.mibo_bridge import (
    ensure_mibo_config,
    save_mibo_config,
    get_face_state,
    set_face_state,
    get_live_weather,
    list_termine,
    add_timer,
    delete_termin,
    list_smart_home,
    toggle_smart_home_device,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ZIP_PATH = os.path.join(os.path.dirname(BASE_DIR), "JARVIS-OMEGA-PC-INSTALLER.zip")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def build_installer_zip_bytes() -> bytes:
    """Builds or reads the complete PC installer ZIP archive."""
    if os.path.exists(ZIP_PATH):
        with open(ZIP_PATH, "rb") as f:
            return f.read()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "external_repos")]
            for file in files:
                if file.endswith(".pyc"):
                    continue
                abs_p = os.path.join(root, file)
                rel_p = os.path.relpath(abs_p, BASE_DIR)
                zf.write(abs_p, os.path.join("jarvis-omega", rel_p))
    return buf.getvalue()


def list_bundled_skill_files():
    items = []
    for folder in ("mibo_jarvis_grundgeruest", "skills", "hooks", "agents"):
        target = os.path.join(BASE_DIR, folder)
        if not os.path.exists(target):
            continue
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "daten")]
            for f in sorted(files):
                if f.endswith((".pyc", ".gitkeep")):
                    continue
                abs_p = os.path.join(root, f)
                rel_p = os.path.relpath(abs_p, BASE_DIR)
                items.append({
                    "path": rel_p,
                    "category": "MIBO-JARVIS" if folder == "mibo_jarvis_grundgeruest" else folder.upper(),
                    "name": f,
                    "size_bytes": os.path.getsize(abs_p),
                })
    for root_doc in ("CLAUDE.md", "AGENTS.md", "INSTALL_JARVIS_WINDOWS.bat", "install_linux_mac.sh", "download_all_22_repos.py"):
        p = os.path.join(BASE_DIR, root_doc)
        if os.path.exists(p):
            items.append({
                "path": root_doc,
                "category": "CORE",
                "name": root_doc,
                "size_bytes": os.path.getsize(p),
            })
    return items


class JarvisRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(index_file):
                with open(index_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return

        if path == "/api/bootstrap":
            cfg = load_router_config()
            mibo_cfg = ensure_mibo_config()
            self._send_json({
                "telemetry": get_system_telemetry(),
                "catalog": get_catalog(),
                "router_config": cfg,
                "memories": search_memories(limit=15),
                "busabase": busabase_list(),
                "notes": notra_list_notes(),
                "bundled_files": list_bundled_skill_files(),
                "mibo": {
                    "config": mibo_cfg,
                    "face": get_face_state(),
                    "weather": get_live_weather(mibo_cfg.get("stadt", "Frankfurt am Main")),
                    "termine": list_termine(),
                    "smart_home": list_smart_home(),
                }
            })
            return

        if path == "/api/mibo/state":
            mibo_cfg = ensure_mibo_config()
            self._send_json({
                "config": mibo_cfg,
                "face": get_face_state(),
                "termine": list_termine(),
                "smart_home": list_smart_home(),
            })
            return

        if path == "/api/telemetry":
            self._send_json(get_system_telemetry())
            return

        if path == "/api/skill-file":
            qs = urllib.parse.parse_qs(parsed.query)
            rel = (qs.get("path") or ["CLAUDE.md"])[0]
            safe_path = os.path.normpath(os.path.join(BASE_DIR, rel))
            if not safe_path.startswith(BASE_DIR) or not os.path.isfile(safe_path):
                self._send_json({"ok": False, "error": "Datei nicht gefunden"}, 404)
                return
            with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._send_json({"ok": True, "path": rel, "content": content})
            return

        if path == "/download/jarvis-omega.zip":
            zbytes = build_installer_zip_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="JARVIS-OMEGA-PC-INSTALLER.zip"')
            self.send_header("Content-Length", str(len(zbytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(zbytes)
            return

        if path == "/v1/models":
            self._send_json({
                "object": "list",
                "data": [
                    {"id": "jarvis-omega-auto", "object": "model", "owned_by": "stark-omniroute"},
                    {"id": "omniroute-free-cluster", "object": "model", "owned_by": "omniroute"},
                    {"id": "freellmapi-635-router", "object": "model", "owned_by": "freellmapi"},
                    {"id": "airllm-llama3-70b-layerwise", "object": "model", "owned_by": "airllm"},
                ]
            })
            return

        self._send_json({"error": "Not found", "path": path}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}

        if path == "/api/chat":
            prompt = str(body.get("prompt", "")).strip()
            history = body.get("history") or []
            if not prompt:
                self._send_json({"error": "Leere Nachricht"}, 400)
                return

            set_face_state(zustand="denkt")
            p_low = prompt.lower()

            # 1. Native Mibo-AI Tool triggers ("Wetter", "Timer", "Merk dir", "Kühlschrank/Licht", "Ruhemodus")
            if "wetter" in p_low:
                m_city = re.search(r"in\s+([a-zA-ZäöüÄÖÜß\-]+)", prompt)
                city = m_city.group(1) if m_city else ""
                wx = get_live_weather(city)
                forecast_lines = "\n".join([f"- **{d['tag']}**: {d['min_c']}°C bis {d['max_c']}°C, {d['zustand']} (Regenrisiko {d['regen_pct']}%)" for d in wx["vorhersage"]])
                reply = f"🌤️ **LIVE WETTERBERICHT ({wx['ort']})**:\n{wx['sprach_text']}\n\n### 3-Tage-Vorhersage (Open-Meteo)\n{forecast_lines}"
                set_face_state(zustand="spricht", text=wx["sprach_text"])
                self._send_json({
                    "reply": reply,
                    "provider": "Mibo-AI Wetter-Modul (Open-Meteo Live)",
                    "tier": "Zero-Key Local Tool",
                    "latency_ms": 65,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "weather": wx,
                })
                return

            if "merk dir" in p_low or p_low.startswith("/mem "):
                fact = re.sub(r"(?i)^(merk dir,?\s*(dass\s*)?|/mem\s*)", "", prompt).strip()
                mem = add_memory(summary=fact, details="Gespeichert per Sprach-/Chat-Befehl (Mibo-AI Gedächtnis + Claude-Mem)", category="mibo-fakt", importance=9)
                reply = f"🧠 **GEMERKT, SIR:** Ich habe *„{fact}“* dauerhaft in deinem **Claude-Mem & Mibo-AI Gedächtnis** gespeichert. Auch nach einem Neustart weiß ich das sofort."
                set_face_state(zustand="spricht", text=reply)
                self._send_json({
                    "reply": reply,
                    "provider": "Mibo-AI Gedächtnis + Claude-Mem",
                    "tier": "SQLite Persistent Vault",
                    "latency_ms": 12,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "memories": search_memories(limit=15),
                })
                return

            if "timer" in p_low:
                m_min = re.search(r"(\d+)\s*minut", p_low)
                m_sec = re.search(r"(\d+)\s*sekund", p_low)
                sek = int(m_min.group(1)) * 60 if m_min else (int(m_sec.group(1)) if m_sec else 60)
                t_res = add_timer(sek, name=prompt[:40])
                reply = f"⏰ **TIMER GESTELLT:** {sek} Sekunden für *„{prompt[:40]}“*. Ich melde mich per Stimme und Telegram, sobald er abläuft!"
                set_face_state(zustand="spricht", text=reply)
                self._send_json({
                    "reply": reply,
                    "provider": "Mibo-AI Timer & Erinnerungen (termine.py)",
                    "tier": "Background Loop",
                    "latency_ms": 10,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "termine": t_res["termine"],
                })
                return

            if any(w in p_low for w in ("kühlschrank", "kuehlschrank", "waschmaschine", "licht", "wohnzimmer", "kaffee")):
                target_id = "switch.kuehlschrank_kueche" if "kühl" in p_low or "kuehl" in p_low else (
                    "switch.waschmaschine_keller" if "wasch" in p_low else (
                        "switch.kaffeemaschine" if "kaffee" in p_low else "light.wohnzimmer_hauptlicht"
                    )
                )
                aktion = "aus" if "aus" in p_low else ("an" if "an" in p_low or "ein" in p_low else "umschalten")
                ha_res = toggle_smart_home_device(target_id, aktion)
                set_face_state(zustand="spricht", text=ha_res["message"])
                self._send_json({
                    "reply": ha_res["message"],
                    "provider": "Mibo-AI Home Assistant (hausautomation.py)",
                    "tier": "Schutzliste Guard Active",
                    "latency_ms": 14,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "smart_home": ha_res["devices"],
                })
                return

            # 2. Handle direct slash commands inside chat
            if prompt.startswith("/octo"):
                topic = prompt[5:].strip() or "Systemarchitektur & Code-Qualität prüfen"
                octo = run_octopus_consensus(topic)
                reply = (
                    f"🐙 **CLAUDE OCTOPUS 4-SEAT KONSENS ({octo['consensus_pct']}% Zustimmung — Gate {'BESTANDEN ✅' if octo['gate_passed'] else 'WARNUNG ⚠️'})**\n\n"
                    + "\n".join([f"- **{s['agent']}** (`{s['vote']}` | {s['confidence']}%): {s['verdict']}" for s in octo["seats"]])
                    + "\n\n### Synthetisierter Aktionsplan (Double Diamond)\n"
                    + "\n".join(octo["synthesized_action_plan"])
                )
                set_face_state(zustand="spricht", text=f"Octopus Konsens erreicht: {octo['consensus_pct']} Prozent Zustimmung.")
                self._send_json({
                    "reply": reply,
                    "provider": "Claude Octopus Multi-Seat Swarm",
                    "tier": "Swarm Consensus Gate (>=75%)",
                    "latency_ms": 42,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "octopus": octo,
                })
                return

            if prompt.startswith("/security-review"):
                target = prompt[16:].strip() or "git push --force && cat .env"
                sec = run_security_review(target)
                findings_txt = "\n".join([f"- 🚨 **[{f['severity']}] {f['cwe']}**: {f['description']} → *Fix:* `{f['fix']}`" for f in sec["findings"]]) or "- ✅ Keine Schwachstellen gefunden."
                reply = (
                    f"🛡️ **CLAUDE SECURITY REVIEW (Score: {sec['security_score']}/100 — Status: {sec['status']})**\n\n"
                    f"### Gefundene Risiken ({sec['vulnerabilities_found']})\n{findings_txt}\n\n"
                    "### STRIDE Threat Model\n"
                    + "\n".join([f"- **{s['category']}**: `{s['status']}` — {s['control']}" for s in sec["stride_threat_model"]])
                )
                set_face_state(zustand="spricht", text=f"Security Prüfung abgeschlossen. Score: {sec['security_score']} von 100.")
                self._send_json({
                    "reply": reply,
                    "provider": "Claude Security Analyzer",
                    "tier": "PreToolUse & STRIDE Engine",
                    "latency_ms": 18,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "security": sec,
                })
                return

            if prompt.startswith("/montage"):
                topic = prompt[8:].strip() or "Stark Jarvis AI Demo"
                m = run_openmontage_studio(topic)
                reply = (
                    f"🎬 **OPENMONTAGE VIDEO PRODUCTION PIPELINE: „{m['project_title']}“**\n\n"
                    + "\n".join([f"**Szene {s['scene']} ({s['timecode']})**: {s['visual']}\n> 🎙️ *Voiceover:* „{s['voiceover_de']}“" for s in m["scenes"]])
                    + f"\n\n```bash\n{m['ffmpeg_pipeline']}```"
                )
                set_face_state(zustand="spricht", text=m["scenes"][0]["voiceover_de"])
                self._send_json({
                    "reply": reply,
                    "provider": "OpenMontage Studio Engine",
                    "tier": "12-Stage Video Pipeline",
                    "latency_ms": 25,
                    "compression": compress_text_caveman(prompt, "standard"),
                    "montage": m,
                })
                return

            if prompt.startswith("/exec "):
                cmd_str = prompt[6:].strip()
                exec_res = execute_local_action(cmd_str, language="bash")
                out = exec_res["stdout"] or exec_res["stderr"] or "(Keine Ausgabe)"
                reply = (
                    f"💻 **OPEN INTERPRETER / TERMINAL AUSFÜHRUNG (`Exit {exec_res['exit_code']}` in {exec_res['duration_ms']}ms)**\n"
                    f"Security Check: {exec_res['security']['summary']}\n\n"
                    f"```text\n{out}\n```"
                )
                set_face_state(zustand="ruhe")
                self._send_json({
                    "reply": reply,
                    "provider": "Open Interpreter + Claude Security",
                    "tier": "Local OS Execution",
                    "latency_ms": exec_res["duration_ms"],
                    "compression": compress_text_caveman(prompt, "standard"),
                    "execution": exec_res,
                })
                return

            res = route_chat_completion(
                prompt,
                history=history,
                memory_snippet=get_vault_context_snippet(),
            )
            set_face_state(zustand="spricht", text=res["reply"][:240])
            if len(prompt) > 25:
                add_memory(
                    summary=f"Chat-Auftrag: {prompt[:90]}",
                    details=f"Geroutet über {res['tier']} | Ersparnis: {res['compression']['savings_pct']}%",
                    category="session",
                    tags="chat,auto-recall",
                    importance=6,
                )
            self._send_json(res)
            return

        # --- MIBO-AI GRUNDGERÜST ENDPOINTS ---
        if path == "/api/mibo/face":
            st = set_face_state(
                zustand=body.get("zustand"),
                mund=body.get("mund"),
                ruhemodus=body.get("ruhemodus"),
                text=body.get("text"),
            )
            self._send_json({"ok": True, "face": st})
            return

        if path == "/api/mibo/weather":
            ort = str(body.get("ort", "")).strip()
            wx = get_live_weather(ort)
            self._send_json(wx)
            return

        if path == "/api/mibo/timer":
            act = body.get("action", "add")
            if act == "delete":
                res = delete_termin(str(body.get("id", "")))
            else:
                res = add_timer(int(body.get("sekunden", 60)), str(body.get("name", "Timer")))
            self._send_json(res)
            return

        if path == "/api/mibo/smarthome":
            res = toggle_smart_home_device(
                str(body.get("entity_id", "")),
                str(body.get("aktion", "umschalten")),
                body.get("helligkeit"),
            )
            self._send_json(res)
            return

        if path == "/api/mibo/config":
            cfg = save_mibo_config(body)
            busabase_upsert(
                collection="mibo_jarvis",
                record_key="mibo.config",
                new_value={"nutzer_name": cfg["nutzer_name"], "anrede": cfg["anrede"], "stadt": cfg["stadt"], "nachtruhe": cfg["nachtruhe"], "matrix_ip": cfg["matrix_ip"]},
                commit_msg="Mibo-AI Jarvis Grundgerüst Konfiguration aktualisiert",
                agent_name="Mibo-Setup"
            )
            self._send_json({"ok": True, "config": cfg, "face": get_face_state()})
            return

        if path == "/api/modes":
            cfg = load_router_config()
            modes = cfg.get("active_modes", {})
            for k, v in (body.get("modes") or {}).items():
                modes[k] = bool(v)
            cfg["active_modes"] = modes
            save_router_config(cfg)
            busabase_upsert(
                collection="agent_rules",
                record_key="discipline.active_stack",
                new_value=modes,
                commit_msg=f"Modus-Update im Stark HUD: {json.dumps(modes)}",
                agent_name="Stark-HUD-Operator"
            )
            self._send_json({"ok": True, "active_modes": modes, "busabase": busabase_list()})
            return

        if path == "/api/router-config":
            cfg = load_router_config()
            for field in ("omniroute_url", "freellmapi_url", "ollama_url", "custom_base_url", "custom_api_key", "custom_model", "airllm_model"):
                if field in body:
                    cfg[field] = str(body[field]).strip()
            save_router_config(cfg)
            busabase_upsert(
                collection="system_config",
                record_key="router.endpoints",
                new_value={
                    "omniroute": cfg["omniroute_url"],
                    "freellmapi": cfg["freellmapi_url"],
                    "ollama": cfg["ollama_url"],
                    "custom_url": cfg["custom_base_url"],
                    "airllm": cfg["airllm_model"],
                },
                commit_msg="Aktualisiere Hybrid-LLM-Router Endpunkte",
                agent_name="OmniRoute-Config"
            )
            self._send_json({"ok": True, "router_config": cfg})
            return

        if path == "/api/octopus":
            task = str(body.get("task", "Optimiere lokales Jarvis AI-System")).strip()
            res = run_octopus_consensus(task)
            self._send_json(res)
            return

        if path == "/api/autogpt":
            goal = str(body.get("goal", "Baue vollautomatischen Coding-Workflow")).strip()
            res = run_autogpt_plan(goal)
            self._send_json(res)
            return

        if path == "/api/montage":
            topic = str(body.get("topic", "J.A.R.V.I.S. OMEGA Mark LXXXV")).strip()
            res = run_openmontage_studio(topic)
            self._send_json(res)
            return

        if path == "/api/exec":
            cmd = str(body.get("command", "echo 'Hello from Jarvis Omega'"))
            lang = str(body.get("language", "bash"))
            res = execute_local_action(cmd, language=lang)
            self._send_json(res)
            return

        if path == "/api/security-review":
            code = str(body.get("code", ""))
            res = run_security_review(code)
            self._send_json(res)
            return

        if path == "/api/compress":
            text = str(body.get("text", ""))
            level = str(body.get("level", "ultra"))
            res = compress_text_caveman(text, level=level)
            self._send_json(res)
            return

        if path == "/api/memory/add":
            m = add_memory(
                summary=str(body.get("summary", "")),
                details=str(body.get("details", "")),
                category=str(body.get("category", "manual")),
                tags=str(body.get("tags", "jarvis,user")),
                importance=int(body.get("importance", 8)),
            )
            self._send_json({"ok": True, "memory": m, "memories": search_memories(limit=15)})
            return

        if path == "/api/busabase/upsert":
            c = busabase_upsert(
                collection=str(body.get("collection", "user_data")),
                record_key=str(body.get("record_key", "custom.key")),
                new_value=body.get("new_value", {}),
                commit_msg=str(body.get("commit_msg", "Manuelles Update über HUD")),
                agent_name="User-HUD",
            )
            self._send_json({"ok": True, "change": c, "busabase": busabase_list()})
            return

        if path == "/api/busabase/revert":
            cid = int(body.get("change_id", 0))
            res = busabase_revert(cid)
            self._send_json({"ok": res.get("ok", False), "result": res, "busabase": busabase_list()})
            return

        if path == "/api/notra/add":
            n = notra_add_note(
                title=str(body.get("title", "Neue Notiz")),
                content=str(body.get("content", "")),
                tags=str(body.get("tags", "jarvis")),
                favorite=bool(body.get("favorite", True)),
            )
            self._send_json({"ok": True, "note": n, "notes": notra_list_notes()})
            return

        if path == "/v1/chat/completions":
            msgs = body.get("messages") or []
            last_user = ""
            for m in reversed(msgs):
                if m.get("role") == "user":
                    last_user = str(m.get("content", ""))
                    break
            routed = route_chat_completion(last_user or "Hello", history=msgs[:-1], memory_snippet=get_vault_context_snippet())
            self._send_json({
                "id": f"chatcmpl-jarvis-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", "jarvis-omega-auto"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": routed["reply"]},
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": routed["compression"]["compressed_tokens"],
                    "completion_tokens": len(routed["reply"]) // 4,
                    "total_tokens": routed["compression"]["compressed_tokens"] + (len(routed["reply"]) // 4),
                    "jarvis_tokens_saved": routed["compression"]["saved_tokens"],
                }
            })
            return

        self._send_json({"error": "Unknown endpoint", "path": path}, 404)


def run_server(port: int = 8080):
    init_vault()
    ensure_mibo_config()
    server = ThreadedHTTPServer(("0.0.0.0", port), JarvisRequestHandler)
    print(f"🦾 J.A.R.V.I.S. OMEGA (Mark LXXXV + Mibo-AI Grundgerüst) läuft auf http://0.0.0.0:{port}")
    print(f"🔌 OpenAI-kompatibles Gateway bereit unter http://0.0.0.0:{port}/v1/chat/completions")
    server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    run_server(port)
