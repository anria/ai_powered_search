# pages/feedback.py
"""
File-backed store for assistant responses and their judgements.

Data file: <projectroot>/data/assistant_responses.json
Shape:     list of {timestamp, judgement, prompt, answer, approved}
           judgement: 1 = thumbs up, 0 = thumbs down
           approved:  True / False / None (unreviewed)
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

_lock = threading.Lock()


def _path() -> Path:
    root = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    p = root / "data" / "assistant_responses.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("[]", encoding="utf-8")
    return p


def load_all() -> list:
    with _lock:
        try:
            return json.loads(_path().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []


def _save_all(records: list) -> None:
    with _lock:
        _path().write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def append(prompt: str, answer: str, judgement: int, notes: str = "") -> dict:
    """Append a new feedback record. Returns the full record."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "judgement": int(judgement),   # 1 or 0
        "prompt": prompt,
        "answer": answer,
        "approved": None,              # not yet reviewed by admin
        "notes": notes or "",          # <-- new
    }
    with _lock:
        records = []
        try:
            records = json.loads(_path().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            records = []
        records.append(record)
        _path().write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    return record


def update_approved(idx: int, approved: bool) -> dict | None:
    """Set the approved flag on record at index `idx`. Returns the updated record."""
    records = load_all()
    if idx < 0 or idx >= len(records):
        return None
    records[idx]["approved"] = bool(approved)
    _save_all(records)
    return records[idx]


def update_notes(idx: int, notes: str) -> dict | None:
    """Set the notes on record at index `idx`. Returns the updated record."""
    records = load_all()
    if idx < 0 or idx >= len(records):
        return None
    records[idx]["notes"] = str(notes)[:4000]
    _save_all(records)
    return records[idx]    