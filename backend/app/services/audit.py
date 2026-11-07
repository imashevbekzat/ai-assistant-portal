"""Аудит-лог запросов и ответов ассистента (NFR: безопасность)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from ..config import settings


def log_event(event: dict) -> None:
    try:
        path = settings.audit_log_path
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
