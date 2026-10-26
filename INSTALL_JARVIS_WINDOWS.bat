@echo off
chcp 65001 >nul
title J.A.R.V.I.S. OMEGA (Mark LXXXV) — Vollautomatischer PC-Installer
color 0B

echo ============================================================================
echo   🦾 J.A.R.V.I.S. OMEGA (MARK LXXXV) — STARK INDUSTRIES LOCAL AI INSTALLER
echo   Vereint 22 GitHub Open-Source AI/Agent-Projekte in einem lokalen System
echo ============================================================================
echo.

REM 1. Prüfe Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python 3 wurde nicht gefunden. Versuche automatische Installation via winget...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
)

REM 2. Prüfe Git
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Git wurde nicht gefunden. Versuche automatische Installation via winget...
    winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
)

REM 3. Kopiere globale Agent-Regeln (CLAUDE.md & AGENTS.md) in Benutzerprofil
echo [1/4] Installiere Karpathy, Ponytail, Caveman, ADHD ^& Claude Security Regeln...
if not exist "%USERPROFILE%\.claude" mkdir "%USERPROFILE%\.claude"
if not exist "%USERPROFILE%\.codex" mkdir "%USERPROFILE%\.codex"
copy /Y "CLAUDE.md" "%USERPROFILE%\.claude\CLAUDE.md" >nul
copy /Y "AGENTS.md" "%USERPROFILE%\.codex\AGENTS.md" >nul
echo       -^> Globale Regeln in %USERPROFILE%\.claude\CLAUDE.md und .codex\AGENTS.md aktiviert!

REM 4. Optionales Klonen aller 22 GitHub-Repositories
echo.
echo [2/4] Möchtest du jetzt alle 22 Original-GitHub-Repos (~1.2 GB) klonen
echo       oder direkt im Express-Modus starten (alle Kern-Skills sind bereits integriert)?
set /p CLONE_CHOICE="Eingabe [E = Express-Start (Empfohlen) / V = Alle 22 Repos klonen]: "
if /I "%CLONE_CHOICE%"=="V" (
    python download_all_22_repos.py
) else (
    echo       -^> Express-Modus aktiv: Nutze vorintegrierte Skills, Hooks ^& Jarvis-Core!
)

REM 5. Optionale Python-Pakete (Open Interpreter / AirLLM)
echo.
echo [3/4] Prüfe lokale Datenbank (Claude-Mem + Busabase + Notra)...
python jarvis_cli.py doctor

REM 6. Starte J.A.R.V.I.S. OMEGA Stark HUD Server & öffne Browser
echo.
echo [4/4] Starte J.A.R.V.I.S. OMEGA Stark HUD Server auf http://localhost:8080 ...
start "" "http://localhost:8080"
python jarvis_server.py
pause
