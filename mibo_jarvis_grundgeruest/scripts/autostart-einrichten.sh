#!/usr/bin/env bash
# Jarvis bei jeder Anmeldung automatisch starten (Linux mit GNOME, KDE, XFCE ...).
# Rueckgaengig: die Datei ~/.config/autostart/jarvis.desktop loeschen.

ORDNER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/jarvis.desktop" <<EOD
[Desktop Entry]
Type=Application
Name=Jarvis
Comment=Persoenlicher KI-Assistent
Exec=bash "$ORDNER/scripts/starten.sh"
X-GNOME-Autostart-enabled=true
EOD
echo "Autostart eingerichtet: Jarvis startet ab der naechsten Anmeldung von selbst."
