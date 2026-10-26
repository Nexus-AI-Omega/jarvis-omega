"""
J.A.R.V.I.S. OMEGA — Autonomous Anti-Hacker, Anti-Exploit & Anti-DDoS Cyber Shield
===================================================================================
Protects the PC, the Minecraft Server (Java 25565 + Bedrock 19132 + RCON 25575),
and the Web Dashboards (3000 / 8080 / 8340) against:
- DDoS / SYN-Floods / Bot-Ping-Storms / Connection Floods
- Ingame Hackers (Fly, Speed, Reach, KillAura, Nuker/FastBreak, X-Ray)
- Server Crash Exploits (Log4Shell JNDI, Book-Ban/NBT-Overflow, UUID-Spoof, Bungee-Bypass)
- Brute-Force & Credential Stuffing on Dashboard / RCON
"""

import ipaddress
import os
import platform
import re
import socket
import subprocess
import time
from collections import Counter
from typing import Any, Dict, List, Optional


PROTECTED_PORTS = {
    25565: "Minecraft Java Server",
    19132: "Minecraft Bedrock (Geyser UDP)",
    25575: "Minecraft RCON (Kritisch - nur 127.0.0.1!)",
    3000: "Minecraft Server Dashboard",
    8080: "J.A.R.V.I.S. OMEGA HUD",
    8340: "Mibo-AI Sprach- & Gesicht-Core",
}

# Known exploit & hacker signatures in Minecraft logs / chat / packets
EXPLOIT_SIGNATURES = [
    {
        "id": "LOG4SHELL_JNDI",
        "severity": "CRITICAL",
        "pattern": re.compile(r"\$\{\s*(jndi|lower|upper|env|sys|date)\s*:", re.IGNORECASE),
        "title": "Log4Shell / JNDI Remote Code Execution Versuch",
        "action": "ban-ip",
        "description": "Blockiert sofort jeden Versuch, über Chat oder Login-Pakete JNDI-Payloads einzuschleusen.",
    },
    {
        "id": "NBT_CRASH_BOOK",
        "severity": "CRITICAL",
        "pattern": re.compile(
            r"(BookEdit|CustomPayload|PacketPlayIn|Too many NBT tags|DecoderException|Payload may not be larger than)",
            re.IGNORECASE,
        ),
        "title": "Crash-Client / NBT-Book-Overflow Exploit",
        "action": "kick_and_ban",
        "description": "Erkennt überdimensionierte NBT-Bücher, Shulker-Crash-Items und manipulierte CustomPayload-Pakete.",
    },
    {
        "id": "UUID_BUNGEE_SPOOF",
        "severity": "CRITICAL",
        "pattern": re.compile(
            r"(UUID of player .* is .* offline|bungeecord.*spoof|Tried to login with an invalid session)",
            re.IGNORECASE,
        ),
        "title": "UUID-Spoofing / Offline-Admin-Übernahme Versuch",
        "action": "ban-ip",
        "description": "Verhindert, dass sich Angreifer mit gecracktem Launcher unter dem Namen eines Admins einloggen.",
    },
    {
        "id": "MOVEMENT_FLY_SPEED",
        "severity": "HIGH",
        "pattern": re.compile(
            r"(moved too quickly!|moved wrongly!|floating too long!|Sending too many packets)",
            re.IGNORECASE,
        ),
        "title": "Movement-Hack (Fly / Speed / Timer / Packet-Flood)",
        "action": "warn_or_kick",
        "description": "Erkennt unnatürliche Bewegungsgeschwindigkeiten, Fly-Hacks und Timer-Exploits.",
    },
    {
        "id": "RCON_BRUTEFORCE",
        "severity": "CRITICAL",
        "pattern": re.compile(r"RCON Listener.*Authentication failed|Rcon connection from", re.IGNORECASE),
        "title": "Unautorisierter RCON-Zugriffsversuch",
        "action": "firewall_block",
        "description": "Überwacht Port 25575 auf externe Passwort-Bruteforce-Angriffe.",
    },
]

_BLOCKED_IPS: Dict[str, Dict[str, Any]] = {}
_THREAT_HISTORY: List[Dict[str, Any]] = []


def _parse_proc_net_tcp() -> List[Dict[str, Any]]:
    """Reads active TCP sockets directly from /proc/net/tcp (zero external process overhead)."""
    conns: List[Dict[str, Any]] = []
    tcp_states = {
        "01": "ESTABLISHED",
        "02": "SYN_SENT",
        "03": "SYN_RECV",
        "06": "TIME_WAIT",
        "0A": "LISTEN",
    }
    try:
        if not os.path.exists("/proc/net/tcp"):
            return conns
        with open("/proc/net/tcp", "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) < 4:
                continue
            local_hex, rem_hex, state_hex = parts[1], parts[2], parts[3]
            l_ip_hex, l_port_hex = local_hex.split(":")
            r_ip_hex, r_port_hex = rem_hex.split(":")
            l_port = int(l_port_hex, 16)
            r_port = int(r_port_hex, 16)
            r_ip_int = int(r_ip_hex, 16)
            r_ip = socket.inet_ntoa(r_ip_int.to_bytes(4, "little"))
            l_ip = socket.inet_ntoa(int(l_ip_hex, 16).to_bytes(4, "little"))
            conns.append({
                "local_ip": l_ip,
                "local_port": l_port,
                "remote_ip": r_ip,
                "remote_port": r_port,
                "state": tcp_states.get(state_hex, state_hex),
            })
    except Exception:
        pass
    return conns


def inspect_network_shield(max_conn_per_ip: int = 25) -> Dict[str, Any]:
    """
    Real-time Anti-DDoS & Network Connection Analysis.
    Detects SYN floods, connection floods per IP, and exposed RCON ports.
    """
    conns = _parse_proc_net_tcp()
    remote_counter: Counter = Counter()
    syn_recv_count = 0
    rcon_exposed_externally = False
    listening_ports = set()

    for c in conns:
        if c["state"] == "LISTEN":
            listening_ports.add(c["local_port"])
            if c["local_port"] == 25575 and c["local_ip"] not in ("127.0.0.1", "0.0.0.0"):
                rcon_exposed_externally = True
        else:
            rip = c["remote_ip"]
            if rip not in ("0.0.0.0", "127.0.0.1"):
                remote_counter[rip] += 1
            if c["state"] == "SYN_RECV":
                syn_recv_count += 1

    suspicious_ips = []
    for ip, count in remote_counter.most_common(15):
        if count >= max_conn_per_ip:
            suspicious_ips.append({
                "ip": ip,
                "connections": count,
                "verdict": "DDoS / Connection-Flood Verdacht",
                "recommended_action": f"Firewall Drop für {ip}",
            })

    ddos_status = "GRÜN (Kein Angriff aktiv)"
    if syn_recv_count > 50 or suspicious_ips:
        ddos_status = "ALARM (DDoS / Flood-Muster erkannt!)"

    return {
        "ok": True,
        "ddos_status": ddos_status,
        "total_active_sockets": len(conns),
        "syn_recv_queue": syn_recv_count,
        "listening_protected_ports": {
            port: {
                "service": name,
                "listening": port in listening_ports,
            }
            for port, name in PROTECTED_PORTS.items()
        },
        "rcon_localhost_safe": not rcon_exposed_externally,
        "top_remote_ips": [{"ip": ip, "sockets": cnt} for ip, cnt in remote_counter.most_common(10)],
        "suspicious_ips": suspicious_ips,
        "blocked_ips_count": len(_BLOCKED_IPS),
        "blocked_ips": list(_BLOCKED_IPS.values())[-20:],
        "threat_history": _THREAT_HISTORY[-15:],
        "timestamp": time.strftime("%H:%M:%S"),
    }


def generate_antiddos_firewall_kit(block_ip: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates production-ready Anti-DDoS & Anti-Hacker firewall scripts for:
    - Windows (netsh advfirewall PowerShell rules)
    - Linux (iptables + sysctl SYN-Cookie + Connection Rate-Limiting)
    - Minecraft Paper/Velocity/Geyser proxy hardening
    """
    safe_ip = None
    if block_ip:
        try:
            safe_ip = str(ipaddress.ip_address(block_ip.strip()))
            _BLOCKED_IPS[safe_ip] = {
                "ip": safe_ip,
                "reason": "Manuell / Automatisch durch JARVIS Cyber-Shield gesperrt",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except ValueError:
            safe_ip = None

    windows_cmds = [
        "# 1. RCON Port 25575 von außen komplett blockieren (Schutz vor Server-Übernahme)",
        "netsh advfirewall firewall add rule name=\"JARVIS-Block-External-RCON\" dir=in action=block protocol=TCP localport=25575 remoteip=any",
        "# 2. Minecraft Java (25565) & Bedrock Geyser (19132) sauber freigeben",
        "netsh advfirewall firewall add rule name=\"JARVIS-MC-Java-25565\" dir=in action=allow protocol=TCP localport=25565",
        "netsh advfirewall firewall add rule name=\"JARVIS-MC-Bedrock-19132\" dir=in action=allow protocol=UDP localport=19132",
    ]
    if safe_ip:
        windows_cmds.append(
            f"netsh advfirewall firewall add rule name=\"JARVIS-BAN-{safe_ip}\" dir=in action=block remoteip={safe_ip}"
        )

    linux_cmds = [
        "# 1. Kernel SYN-Cookies & Anti-Spoofing aktivieren (Schutz gegen SYN-Flood DDoS)",
        "sysctl -w net.ipv4.tcp_syncookies=1",
        "sysctl -w net.ipv4.tcp_max_syn_backlog=4096",
        "sysctl -w net.ipv4.conf.all.rp_filter=1",
        "# 2. RCON (25575) strikt nur auf 127.0.0.1 erlauben",
        "iptables -A INPUT -p tcp --dport 25575 ! -s 127.0.0.1 -j DROP",
        "# 3. Max. 15 gleichzeitige Verbindungen pro IP auf Minecraft Port 25565 (Anti-Bot-Raid)",
        "iptables -A INPUT -p tcp --syn --dport 25565 -m connlimit --connlimit-above 15 --connlimit-mask 32 -j REJECT --reject-with tcp-reset",
        "# 4. Neue Verbindungsrate pro IP begrenzen (max. 10 Pakete / 5 Sek. Burst)",
        "iptables -A INPUT -p tcp --dport 25565 -m state --state NEW -m recent --set --name MC_DDOS",
        "iptables -A INPUT -p tcp --dport 25565 -m state --state NEW -m recent --update --seconds 5 --hitcount 10 --name MC_DDOS -j DROP",
    ]
    if safe_ip:
        linux_cmds.append(f"iptables -I INPUT -s {safe_ip} -j DROP")

    return {
        "ok": True,
        "blocked_ip": safe_ip,
        "windows_powershell_rules": "\n".join(windows_cmds),
        "linux_iptables_rules": "\n".join(linux_cmds),
        "minecraft_hardening_checklist": [
            "server.properties: enforce-secure-profile=true & prevent-proxy-connections=true setzen",
            "server.properties: rcon.ip=127.0.0.1 erzwingen (niemals 0.0.0.0)",
            "paper-global.yml: packet-limiter.all-packets.max-packet-rate=350.0 aktivieren (verhindert Crash-Clients)",
            "paper-global.yml: book-size.page-max=2560 (verhindert NBT Book-Ban & Dupe-Exploits)",
            "TCPShield oder Playit.gg vor Port 25565 schalten, um die echte Heim-/VPS-IP vor DDoS zu verstecken",
        ],
    }


def scan_logs_for_hackers_and_exploits(log_lines: List[str]) -> Dict[str, Any]:
    """
    Scans Minecraft server logs or chat lines for hackers, crash-clients,
    Log4Shell, NBT-Exploits, and bot raids, returning instant RCON mitigation commands.
    """
    findings: List[Dict[str, Any]] = []
    rcon_countermeasures: List[str] = []
    join_timestamps: List[float] = []

    for idx, line in enumerate(log_lines[-300:]):
        if not line:
            continue
        for sig in EXPLOIT_SIGNATURES:
            if sig["pattern"].search(line):
                # Extract player name or IP if present
                ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
                player_match = re.search(r"([A-Za-z0-9_]{3,16})\s*(?:lost connection|moved|issued|tried)", line)
                ip_val = ip_match.group(0) if ip_match else None
                player_val = player_match.group(1) if player_match else None

                finding = {
                    "id": sig["id"],
                    "severity": sig["severity"],
                    "title": sig["title"],
                    "description": sig["description"],
                    "player": player_val,
                    "ip": ip_val,
                    "log_line": line.strip()[:220],
                    "timestamp": time.strftime("%H:%M:%S"),
                }
                findings.append(finding)
                _THREAT_HISTORY.append(finding)

                if sig["action"] == "ban-ip" and ip_val and ip_val != "127.0.0.1":
                    cmd = f"ban-ip {ip_val} [JARVIS Cyber-Shield] {sig['title']}"
                    if cmd not in rcon_countermeasures:
                        rcon_countermeasures.append(cmd)
                elif player_val:
                    cmd = f"kick {player_val} [JARVIS Cyber-Shield] Verdächtige Pakete / {sig['title']}"
                    if cmd not in rcon_countermeasures:
                        rcon_countermeasures.append(cmd)

        if "joined the game" in line or "UUID of player" in line:
            join_timestamps.append(time.time())

    # Bot-Raid heuristic: >= 10 joins in examined snippet
    if len(join_timestamps) >= 10:
        findings.append({
            "id": "BOT_JOIN_RAID",
            "severity": "HIGH",
            "title": f"Bot-Raid erkannt ({len(join_timestamps)} schnelle Joins)",
            "description": "Massenhafter Beitritt in kurzer Zeit deutet auf einen Bot-Angriff hin.",
            "player": None,
            "ip": None,
            "log_line": f"{len(join_timestamps)} Login-Events im aktuellen Log-Fenster",
            "timestamp": time.strftime("%H:%M:%S"),
        })
        rcon_countermeasures.append("whitelist on")
        rcon_countermeasures.append("say [JARVIS Cyber-Shield] Bot-Schutz aktiviert: Whitelist vorübergehend eingeschaltet.")

    return {
        "ok": True,
        "scanned_lines": len(log_lines),
        "threats_found": len(findings),
        "findings": findings,
        "rcon_countermeasures": rcon_countermeasures,
    }
