@echo off
title J.A.R.V.I.S. OMEGA - Ultra-Low-RAM Minecraft Server (Auto-Restart + Anti-Lag)
:loop
echo [JARVIS] Starte Minecraft Server mit StringDeduplication (-35%% RAM) & Aikar G1GC...
java -Xms3G -Xmx3G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=130 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=28 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=15 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:+UseStringDeduplication -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -jar paper.jar --nogui
echo [JARVIS] Server gestoppt. Automatischer Neustart in 5 Sekunden (STRG+C zum Abbrechen)...
timeout /t 5
goto loop
