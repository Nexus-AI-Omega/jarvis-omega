#!/usr/bin/env python3
"""
Automated Downloader & Integrator for all 22 Open-Source GitHub Repositories
in J.A.R.V.I.S. OMEGA (Mark LXXXV).
Run this on your PC to clone or update all 22 upstream repositories into ./external_repos/
"""

import os
import subprocess
import sys
from jarvis_core.catalog import get_catalog


def clone_all_repos(target_dir: str = "external_repos"):
    os.makedirs(target_dir, exist_ok=True)
    catalog = get_catalog()
    total = len(catalog)
    print("=" * 72)
    print(f"  🚀 J.A.R.V.I.S. OMEGA — AUTO-DOWNLOADER FÜR ALLE {total} GITHUB-REPOS")
    print("=" * 72)

    success = 0
    for idx, item in enumerate(catalog, start=1):
        repo_slug = item["repo"]
        folder_name = item["id"]
        dest_path = os.path.join(target_dir, folder_name)
        print(f"\n[{idx}/{total}] 📦 {item['name']} ({repo_slug})")
        print(f"         Rolle: {item['role_in_jarvis']}")

        if os.path.exists(os.path.join(dest_path, ".git")):
            print(f"         ✅ Bereits vorhanden in {dest_path} — führe git pull aus...")
            subprocess.run(["git", "-C", dest_path, "pull", "--ff-only"], check=False)
            success += 1
            continue

        url = f"https://github.com/{repo_slug}.git"
        try:
            res = subprocess.run(
                ["git", "clone", "--depth", "1", url, dest_path],
                check=False
            )
            if res.returncode == 0:
                print(f"         ✅ Erfolgreich geklont nach {dest_path}")
                success += 1
            else:
                print(f"         ⚠️ Konnte {repo_slug} nicht klonen (Netzwerk/Git prüfen).")
        except Exception as e:
            print(f"         ⚠️ Fehler: {e}")

    print("\n" + "=" * 72)
    print(f"  🎯 FERTIG: {success}/{total} GitHub-Projekte lokal in './{target_dir}/' bereit!")
    print("  💡 Hinweis: Die wichtigsten Skills, Hooks & Regeln sind bereits")
    print("     direkt in './skills/', './hooks/' und './CLAUDE.md' vorinstalliert!")
    print("=" * 72)


if __name__ == "__main__":
    clone_all_repos()
