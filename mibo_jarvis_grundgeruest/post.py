"""Ungelesene E-Mails nachsehen (nur lesen, nichts wird als gelesen markiert).

config.json: "imap_server" (z.B. imap.gmail.com), "email_adresse",
"email_passwort" (bei Gmail/iCloud ein App-Passwort, nicht das normale).
"""

import asyncio
import email
import imaplib
from email.header import decode_header
from email.utils import parseaddr

import konfig


def aktiv() -> bool:
    return bool(konfig.get("imap_server") and konfig.get("email_adresse") and konfig.get("email_passwort"))


def _dec(s) -> str:
    return "".join(t.decode(cs or "utf-8", "replace") if isinstance(t, bytes) else t
                   for t, cs in decode_header(s or ""))


def _ungelesen(anzahl: int) -> str:
    m = imaplib.IMAP4_SSL(konfig.get("imap_server"), 993, timeout=30)
    try:
        m.login(konfig.get("email_adresse"), konfig.get("email_passwort"))
        m.select("INBOX", readonly=True)
        _, d = m.uid("SEARCH", None, "UNSEEN")
        uids = d[0].split()
        if not uids:
            return "Keine ungelesenen Mails."
        zeilen = [f"{len(uids)} ungelesene Mail(s), die neuesten:"]
        for uid in reversed(uids[-anzahl:]):
            _, teil = m.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            h = email.message_from_bytes(teil[0][1])
            name, adr = parseaddr(_dec(h.get("From")))
            zeilen.append(f"- von {name or adr}: {_dec(h.get('Subject')) or '(ohne Betreff)'}")
        return "\n".join(zeilen)
    finally:
        try:
            m.logout()
        except Exception:
            pass


async def ungelesen(anzahl: int = 10) -> str:
    return await asyncio.to_thread(_ungelesen, max(1, min(30, anzahl)))
