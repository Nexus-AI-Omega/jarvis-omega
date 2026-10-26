#!/usr/bin/env python3
"""
J.A.R.V.I.S. OMEGA — Installer-ZIP-Builder
==========================================
Packt das komplette Projekt (Jarvis Omega + Mibo-AI Grundgerüst + Skills/Hooks/Agents
+ generierte Configs/Plugins) in ein sofort entpackbares PC-Installer-Archiv.

Aufruf:
    python3 build_installer.py            # schreibt ../JARVIS-OMEGA-PC-INSTALLER.zip
    python3 build_installer.py --write-local   # zusätzlich ./JARVIS-OMEGA-PC-INSTALLER.zip
"""

import os
import sys
import time
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(os.path.dirname(BASE_DIR), "JARVIS-OMEGA-PC-INSTALLER.zip")
LOCAL_COPY = os.path.join(BASE_DIR, "JARVIS-OMEGA-PC-INSTALLER.zip")

SKIP_DIRS = {"__pycache__", ".git", "external_repos", ".venv", "venv", "node_modules", ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {"JARVIS-OMEGA-PC-INSTALLER.zip"}
SKIP_SUFFIXES = (".pyc", ".pyo", ".log")


def iter_project_files():
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name in SKIP_FILES or name.endswith(SKIP_SUFFIXES):
                continue
            abs_p = os.path.join(root, name)
            rel_p = os.path.relpath(abs_p, BASE_DIR)
            if rel_p.startswith(".git" + os.sep):
                continue
            yield abs_p, rel_p


def build(out_path: str = OUT_PATH) -> str:
    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for abs_p, rel_p in iter_project_files():
            zf.write(abs_p, os.path.join("jarvis-omega", rel_p))
            count += 1
        zf.writestr(
            "jarvis-omega/INSTALL_HINWEIS.txt",
            "J.A.R.V.I.S. OMEGA (Mark LXXXV) — Installationsarchiv\n"
            f"Erstellt: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Dateien: {count}\n\n"
            "WINDOWS:  INSTALL_JARVIS_WINDOWS.bat doppelklicken\n"
            "LINUX/MAC: chmod +x install_linux_mac.sh && ./install_linux_mac.sh\n"
            "DANACH:   python3 jarvis_server.py  ->  http://localhost:8080\n",
        )
        count += 1
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"[OK] {out_path}  ({count} Dateien, {size_mb:.1f} MB)")
    return out_path


if __name__ == "__main__":
    build(OUT_PATH)
    if "--write-local" in sys.argv:
        build(LOCAL_COPY)
