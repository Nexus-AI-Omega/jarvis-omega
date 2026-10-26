"""
Unified Local Memory & Knowledge Vault (SQLite)
Fuses:
1. Claude-Mem (thedotmack/claude-mem) — Episodic Session Memory & Auto-Recall
2. Busabase (busabase/busabase) — Versioned Structured Records with ChangeRequests & 1-Click Revert
3. Notra (MohamedZainAlabdeen/notra) — Local Markdown Notes with Tags & Favorites
"""

import json
import os
import sqlite3
import time
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_vault.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_vault():
    conn = get_conn()
    cur = conn.cursor()

    # 1. Claude-Mem Episodic Memory Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claude_mem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL DEFAULT 'episodic',
            summary TEXT NOT NULL,
            details TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            importance INTEGER NOT NULL DEFAULT 5,
            created_at TEXT NOT NULL
        )
    """)

    # 2. Busabase Versioned Records & ChangeRequests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS busabase_records (
            record_key TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS busabase_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection TEXT NOT NULL,
            record_key TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT NOT NULL,
            commit_msg TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied',
            created_at TEXT NOT NULL
        )
    """)

    # 3. Notra Markdown Notes Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notra_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT 'jarvis,general',
            favorite INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    # Seed initial data if empty
    cur.execute("SELECT COUNT(*) as c FROM claude_mem")
    if cur.fetchone()["c"] == 0:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        seed_memories = [
            ("architecture", "Jarvis Omega vereint 22 GitHub-Projekte in einem lokalen Stark-OS.",
             "Kernmodule: OmniRoute + FreeLLMAPI (Routing), AirLLM (lokale 70B Modelle), Claude-Mem + Busabase + Notra (Gedächtnis), Superpowers + Claude Octopus + Agency-Agents + AutoGPT (Swarm), Open Interpreter + Cline + Goose + Codex (Ausführung), Karpathy + Ponytail + Caveman + i-have-adhd (Regelwerk), Claude Security (Schutzschild).",
             "jarvis,architektur,core", 10, now),
            ("preference", "Nutzer bevorzugt All-in-One Stark-HUD mit Hybrid-LLM-Router (Kostenlos + Lokal + Cloud).",
             "Standardmäßig sind Karpathy-Regeln, Ponytail (YAGNI), i-have-adhd (Action-First) und Claude Security PreToolUse-Hooks aktiviert.",
             "user,config,router", 9, now),
            ("security", "Claude Security Hooks schützen .env, SSH-Keys und blockieren git push --force.",
             "Alle Terminal- und Datei-Aktionen durchlaufen automatisch pre_tool_use_check() vor der Ausführung.",
             "security,hooks,guardrails", 9, now),
        ]
        cur.executemany(
            "INSERT INTO claude_mem (category, summary, details, tags, importance, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            seed_memories
        )

    cur.execute("SELECT COUNT(*) as c FROM busabase_changes")
    if cur.fetchone()["c"] == 0:
        conn.commit()
        busabase_upsert(
            collection="system_config",
            record_key="router.primary_strategy",
            new_value={"tier_1": "FreeLLMAPI + OmniRoute (635 Free Endpoints)", "tier_2": "AirLLM 70B / Ollama Local", "tier_3": "Cloud API Keys", "compression": "RTK + Caveman"},
            commit_msg="Initialisiere Hybrid-LLM-Router mit 4-Tier Auto-Fallback",
            agent_name="OmniRoute-Orchestrator"
        )
        busabase_upsert(
            collection="agent_rules",
            record_key="discipline.active_stack",
            new_value={"karpathy_10_rules": True, "ponytail_level": "full", "adhd_action_first": True, "caveman_compression": "standard", "security_hooks": "strict"},
            commit_msg="Aktiviere Karpathy + Ponytail + ADHD + Claude Security Standard-Regelwerk",
            agent_name="Karpathy-Guard"
        )

    cur.execute("SELECT COUNT(*) as c FROM notra_notes")
    if cur.fetchone()["c"] == 0:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        seed_notes = [
            ("Stark Jarvis Schnellstart & Slash-Befehle",
             "Nutze `/octo <Aufgabe>` für 4-Agenten-Konsens, `/caveman` für bis zu 89% Token-Ersparnis, `/security-review` für Code-Audits, `/montage` für OpenMontage Video-Pipelines und `/exec` für lokale Python/Bash-Ausführung.",
             "quickstart,commands,jarvis", 1, now),
            ("AirLLM 70B auf 4GB/8GB GPU ausführen",
             "Mit `from airllm import AutoModel; model = AutoModel.from_pretrained('meta-llama/Meta-Llama-3-70B-Instruct')` lädt Jarvis riesige 70B-Modelle Schicht für Schicht (Layer-wise Inference) ohne VRAM-Overflow.",
             "airllm,gpu,local-llm", 1, now),
            ("Karpathy + Ponytail + ADHD Golden Rules",
             "1. Zeile 1 = Direkte Aktion/Befehl (i-have-adhd)\n2. Kleinstmöglicher Diff ohne unbestellte Features (Ponytail)\n3. Annahmen offenlegen & Schritt -> Verify (Karpathy)\n4. Null Füllwörter (Caveman)",
             "karpathy,ponytail,adhd,caveman", 1, now),
        ]
        cur.executemany(
            "INSERT INTO notra_notes (title, content, tags, favorite, updated_at) VALUES (?, ?, ?, ?, ?)",
            seed_notes
        )

    conn.commit()
    conn.close()


# --- CLAUDE-MEM FUNCTIONS ---

def add_memory(summary: str, details: str = "", category: str = "episodic", tags: str = "jarvis", importance: int = 7) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO claude_mem (category, summary, details, tags, importance, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (category, summary, details or summary, tags, importance, now)
    )
    mem_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": mem_id, "category": category, "summary": summary, "details": details, "tags": tags, "importance": importance, "created_at": now}


def search_memories(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    if query.strip():
        q = f"%{query.strip()}%"
        cur.execute(
            "SELECT * FROM claude_mem WHERE summary LIKE ? OR details LIKE ? OR tags LIKE ? ORDER BY importance DESC, id DESC LIMIT ?",
            (q, q, q, limit)
        )
    else:
        cur.execute("SELECT * FROM claude_mem ORDER BY importance DESC, id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# --- BUSABASE FUNCTIONS ---

def busabase_upsert(collection: str, record_key: str, new_value: Any, commit_msg: str, agent_name: str = "Jarvis-Core") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT value_json FROM busabase_records WHERE record_key = ?", (record_key,))
    existing = cur.fetchone()
    old_val_str = existing["value_json"] if existing else None
    new_val_str = json.dumps(new_value, ensure_ascii=False) if not isinstance(new_value, str) else new_value

    cur.execute(
        "INSERT OR REPLACE INTO busabase_records (record_key, collection, value_json, updated_at) VALUES (?, ?, ?, ?)",
        (record_key, collection, new_val_str, now)
    )
    cur.execute(
        "INSERT INTO busabase_changes (collection, record_key, old_value, new_value, commit_msg, agent_name, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'applied', ?)",
        (collection, record_key, old_val_str, new_val_str, commit_msg, agent_name, now)
    )
    change_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"change_id": change_id, "record_key": record_key, "status": "applied", "commit_msg": commit_msg}


def busabase_revert(change_id: int) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM busabase_changes WHERE id = ?", (change_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"ok": False, "error": "ChangeRequest nicht gefunden."}

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if row["old_value"] is not None:
        cur.execute(
            "INSERT OR REPLACE INTO busabase_records (record_key, collection, value_json, updated_at) VALUES (?, ?, ?, ?)",
            (row["record_key"], row["collection"], row["old_value"], now)
        )
    else:
        cur.execute("DELETE FROM busabase_records WHERE record_key = ?", (row["record_key"],))

    cur.execute("UPDATE busabase_changes SET status = 'reverted' WHERE id = ?", (change_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "reverted_change_id": change_id, "record_key": row["record_key"]}


def busabase_list() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM busabase_records ORDER BY updated_at DESC")
    records = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM busabase_changes ORDER BY id DESC LIMIT 20")
    changes = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"records": records, "changes": changes}


# --- NOTRA FUNCTIONS ---

def notra_add_note(title: str, content: str, tags: str = "jarvis", favorite: bool = False) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO notra_notes (title, content, tags, favorite, updated_at) VALUES (?, ?, ?, ?, ?)",
        (title, content, tags, 1 if favorite else 0, now)
    )
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": note_id, "title": title, "content": content, "tags": tags, "favorite": favorite, "updated_at": now}


def notra_list_notes(query: str = "", tag: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM notra_notes WHERE 1=1"
    params: List[Any] = []
    if query.strip():
        sql += " AND (title LIKE ? OR content LIKE ?)"
        q = f"%{query.strip()}%"
        params.extend([q, q])
    if tag.strip():
        sql += " AND tags LIKE ?"
        params.append(f"%{tag.strip()}%")
    sql += " ORDER BY favorite DESC, id DESC LIMIT 50"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_vault_context_snippet() -> str:
    """Returns a compact context string for LLM prompt injection."""
    mems = search_memories(limit=4)
    notes = notra_list_notes()[:2]
    lines = ["Erinnerungen (Claude-Mem):"]
    for m in mems:
        lines.append(f"- [{m['category']}] {m['summary']}")
    if notes:
        lines.append("Notizen (Notra):")
        for n in notes:
            lines.append(f"- {n['title']}: {n['content'][:120]}")
    return "\n".join(lines)
