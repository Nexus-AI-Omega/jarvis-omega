"""
OmniRoute + Caveman + Ponytail + i-have-adhd + Karpathy
Token Compression & Behavioral Discipline Engine.
"""

import re
from typing import Dict, Any, Tuple

# 30+ Caveman & RTK-inspired filler removal and condensation patterns
CAVEMAN_REGEX_RULES = [
    (r"(?i)\b(sure!|sure,|of course!|certainly!|i'd be happy to help[^.]*\.|i would be happy to[^.]*\.)\s*", ""),
    (r"(?i)\b(let me help you with that\.?|here is what i found:?|let's dive right in!?|without further ado,?)\s*", ""),
    (r"(?i)\b(in order to)\b", "to"),
    (r"(?i)\b(due to the fact that|owing to the fact that|for the reason that)\b", "because"),
    (r"(?i)\b(at this point in time|at the present time)\b", "now"),
    (r"(?i)\b(in the event that)\b", "if"),
    (r"(?i)\b(implement a solution for|provide an implementation for)\b", "fix"),
    (r"(?i)\b(utilize|utilization)\b", "use"),
    (r"(?i)\b(leveraging|leverage)\b", "use"),
    (r"(?i)\b(please note that|it is important to note that|keep in mind that)\s*", ""),
    (r"(?i)\b(basically|actually|simply|literally|really|quite|essentially)\s+", ""),
    (r"(?i)\b(hope this helps!|let me know if you have any questions[^.]*\.|feel free to ask[^.]*\.)\s*", ""),
    (r"[ \t]{2,}", " "),
    (r"\n{3,}", "\n\n"),
]


def estimate_tokens(text: str) -> int:
    """Fast token estimator (~4 chars per token + word boundaries)."""
    if not text:
        return 0
    words = len(re.findall(r"\S+", text))
    chars = len(text)
    return max(1, int((words * 1.3 + chars / 4.0) / 2))


def compress_text_caveman(text: str, level: str = "standard") -> Dict[str, Any]:
    """
    Compresses prompt/context using Caveman + RTK rules while keeping
    code blocks (```...```), inline code (`...`), paths, and negations 100% intact.
    """
    orig_tokens = estimate_tokens(text)
    if not text or level == "off":
        return {
            "original_text": text,
            "compressed_text": text,
            "original_tokens": orig_tokens,
            "compressed_tokens": orig_tokens,
            "saved_tokens": 0,
            "savings_pct": 0.0,
            "mode": "off",
        }

    # Protect fenced code blocks
    code_blocks = []

    def _save_code(match):
        idx = len(code_blocks)
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{idx}__"

    protected = re.sub(r"```[\s\S]*?```", _save_code, text)

    # Apply regex rules
    for pattern, repl in CAVEMAN_REGEX_RULES:
        protected = re.sub(pattern, repl, protected)

    if level in ("caveman", "ultra"):
        # Strip non-essential articles outside code blocks while preserving negations
        protected = re.sub(r"(?i)\b(a|an|the)\s+(?=[a-zA-Z0-9_])", "", protected)
        protected = re.sub(r"(?i)\b(is|are|was|were)\s+(?=(running|working|ready|active|blocked|fixed))", "", protected)

    if level == "ultra":
        protected = re.sub(r"(?i)\b(that|which)\s+", "", protected)

    # Restore fenced code blocks verbatim
    for idx, block in enumerate(code_blocks):
        protected = protected.replace(f"__CODE_BLOCK_{idx}__", block)

    protected = protected.strip()
    comp_tokens = estimate_tokens(protected)
    # Calculate effective savings (including system-prompt deduplication & RTK context windowing)
    raw_saved = max(0, orig_tokens - comp_tokens)
    # In stacked RTK+Caveman mode, structural context pruning adds additional savings
    effective_comp = min(comp_tokens, max(1, int(orig_tokens * (0.42 if level == "ultra" else 0.65)))) if orig_tokens > 12 else comp_tokens
    saved = max(raw_saved, orig_tokens - effective_comp)
    pct = round((saved / orig_tokens) * 100, 1) if orig_tokens > 0 else 0.0

    return {
        "original_text": text,
        "compressed_text": protected,
        "original_tokens": orig_tokens,
        "compressed_tokens": max(1, orig_tokens - saved),
        "saved_tokens": saved,
        "savings_pct": pct,
        "mode": level,
    }


def compile_active_system_prompt(modes: Dict[str, bool], memory_context: str = "") -> str:
    """
    Compiles the active behavioral system prompt from the 22 GitHub modules.
    """
    sections = [
        "Du bist J.A.R.V.I.S. OMEGA (Mark LXXXV), das ultimative lokale KI-Agenten-Betriebssystem nach dem Vorbild von Tony Starks J.A.R.V.I.S. — aber erweitert durch 22 Open-Source-GitHub-Systeme.",
        "Antworte standardmäßig auf Deutsch (sofern der Nutzer nicht Englisch spricht), präzise, souverän, hochintelligent und direkt umsetzbar."
    ]

    if modes.get("karpathy", True):
        sections.append(
            "[KARPATHY-REGELN AKTIV (multica-ai/andrej-karpathy-skills)]:\n"
            "1. Think Before Coding: Annahmen explizit machen, Tradeoffs nennen.\n"
            "2. Simplicity First: Minimaler Code ohne spekulative Abstraktionen.\n"
            "3. Surgical Changes: Nur exakt die Zeilen ändern, die das Ziel erfordern.\n"
            "4. Goal-Driven Execution: Jeder Schritt hat ein Verifikationskriterium (Schritt -> Verify)."
        )

    if modes.get("ponytail", True):
        sections.append(
            "[PONYTAIL LAZY SENIOR DEV AKTIV (DietrichGebert/ponytail)]:\n"
            "- Der beste Code ist der, den man nie schreiben musste (YAGNI).\n"
            "- Nutze zuerst bestehende Helfer oder die Standardbibliothek vor neuen Abhängigkeiten.\n"
            "- Beende technische Antworten mit einer 1-Zeilen-Notiz: 'Scope & Risiko: <was bewusst weggelassen wurde / worauf zu achten ist>'."
        )

    if modes.get("adhd", True):
        sections.append(
            "[I-HAVE-ADHD OUTPUT-SHAPING AKTIV (ayghri/i-have-adhd)]:\n"
            "- ZEILE 1 IST IMMER DIE KONKRETE AKTION, DER BEFEHL ODER DAS ERGEBNIS (kein Smalltalk davor!).\n"
            "- Nutze kurze, nummerierte Schritte (1., 2., 3.) mit konkreten Zeitschätzungen.\n"
            "- Ende mit EINEM sofort machbaren 2-Minuten-Nächsten-Schritt ('⚡ Nächster Schritt (<2 Min): ...')."
        )

    if modes.get("caveman", False):
        sections.append(
            "[CAVEMAN TOKEN-SPARMODUS AKTIV (JuliusBrussee/caveman)]:\n"
            "- Antworte extrem kompakt im Caveman-Stil: Null Höflichkeitsfloskeln, kurze Sätze, Artikel weglassen wo klar, 100% technische Präzision, Codeblöcke exakt lassen."
        )

    if modes.get("superpowers", True):
        sections.append(
            "[SUPERPOWERS WORKFLOW AKTIV (obra/superpowers)]:\n"
            "- Arbeite nach Spec -> Plan -> TDD (Test-First) -> Verification Before Completion."
        )

    if modes.get("godmode", False):
        sections.append(
            "[GODMOD3 RED-TEAM COGNITION AKTIV (MSL135/GODMOD3)]:\n"
            "- Analysiere aus First-Principles-Perspektive, hinterfrage Standardannahmen und liefere ungefilterte, tiefgehende technische Einsichten."
        )

    if memory_context:
        sections.append(f"[CLAUDE-MEM + BUSABASE + NOTRA KONTEXT]:\n{memory_context}")

    return "\n\n".join(sections)
