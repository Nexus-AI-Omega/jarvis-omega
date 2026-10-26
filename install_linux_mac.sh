#!/usr/bin/env bash
set -e

echo "============================================================================"
echo "  🦾 J.A.R.V.I.S. OMEGA (MARK LXXXV) — LINUX / MACOS AUTO-INSTALLER"
echo "  Vereint 22 GitHub Open-Source AI/Agent-Projekte in einem lokalen System"
echo "============================================================================"

mkdir -p "$HOME/.claude" "$HOME/.codex" "$HOME/.cursor/rules"
cp -f CLAUDE.md "$HOME/.claude/CLAUDE.md"
cp -f AGENTS.md "$HOME/.codex/AGENTS.md"
cp -f CLAUDE.md "$HOME/.cursor/rules/jarvis-omega.mdc"
echo "✅ [1/4] CLAUDE.md & AGENTS.md global in ~/.claude, ~/.codex und ~/.cursor installiert."

if [ "${1:-}" = "--full-clone" ]; then
    echo "📦 [2/4] Klone alle 22 GitHub-Repositories nach ./external_repos/ ..."
    python3 download_all_22_repos.py
else
    echo "⚡ [2/4] Express-Modus: Alle 22 Kern-Skills, Hooks & Router-Module sind bereits integriert!"
    echo "        (Tipp: Starte './install_linux_mac.sh --full-clone' um alle 22 Original-Repos komplett zu klonen)"
fi

echo "🔍 [3/4] Führe System-Diagnose (Karpathy + Claude Security + SQLite Vault) aus..."
python3 jarvis_cli.py doctor

echo "🚀 [4/4] Starte J.A.R.V.I.S. OMEGA Stark HUD auf http://localhost:8080 ..."
python3 jarvis_server.py
