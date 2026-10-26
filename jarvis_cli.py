#!/usr/bin/env python3
"""
J.A.R.V.I.S. OMEGA (Mark LXXXV) — Unified Terminal CLI
Usage:
  python3 jarvis_cli.py status
  python3 jarvis_cli.py doctor
  python3 jarvis_cli.py chat "Baue mir einen lokalen Webscraper"
  python3 jarvis_cli.py octo "Architektur für Multi-Agenten-System"
  python3 jarvis_cli.py compress "Sure! I would be happy to help you implement a solution for that."
  python3 jarvis_cli.py security-check "git push --force origin main"
  python3 jarvis_cli.py clone-all
"""

import json
import sys
from jarvis_core.catalog import get_catalog
from jarvis_core.compression import compress_text_caveman
from jarvis_core.security import pre_tool_use_check, run_security_review
from jarvis_core.memory import init_vault, search_memories, get_vault_context_snippet
from jarvis_core.octopus import run_octopus_consensus
from jarvis_core.executor import get_system_telemetry
from jarvis_core.router import route_chat_completion


def main():
    init_vault()
    args = sys.argv[1:]
    cmd = args[0].lower() if args else "status"
    rest = " ".join(args[1:]).strip()

    if cmd in ("status", "doctor"):
        tel = get_system_telemetry()
        repos = get_catalog()
        mems = search_memories(limit=5)
        print("=" * 68)
        print("  🦾 J.A.R.V.I.S. OMEGA (Mark LXXXV) — SYSTEM DIAGNOSTICS")
        print("=" * 68)
        print(f"  Host / OS       : {tel['hostname']} ({tel['os']})")
        print(f"  Python          : {tel['python_version']} | CPU Cores: {tel['cpu_cores']} ({tel['cpu_load_pct']}% Load)")
        print(f"  RAM             : {tel['ram_used_mb']} MB / {tel['ram_total_mb']} MB ({tel['ram_pct']}%)")
        print(f"  AirLLM Engine   : {tel['airllm_layer_split']}")
        print(f"  GitHub Modules  : {len(repos)} / 22 Fused & Active")
        print(f"  Claude-Mem DB   : {len(mems)} aktive Kern-Erinnerungen geladen")
        print(f"  Claude Security : PreToolUse Hooks (.env + Force-Push Schutz) ONLINE")
        print("=" * 68)
        return

    if cmd == "chat":
        prompt = rest or "Statusbericht, Jarvis!"
        res = route_chat_completion(prompt, memory_snippet=get_vault_context_snippet())
        print(f"[{res['tier']} | Saved {res['compression']['savings_pct']}% Tokens]")
        print(res["reply"])
        return

    if cmd == "octo":
        res = run_octopus_consensus(rest or "Optimiere lokalen AI-Agenten")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if cmd == "compress":
        res = compress_text_caveman(rest or "Sure! I would be happy to help you in order to implement a solution for the database.", level="ultra")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if cmd == "security-check":
        res = run_security_review(rest or "cat .env && git push --force")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if cmd == "clone-all":
        import download_all_22_repos
        download_all_22_repos.clone_all_repos()
        return

    print(f"Unbekannter Befehl: {cmd}. Verfügbar: status, doctor, chat, octo, compress, security-check, clone-all")


if __name__ == "__main__":
    main()
