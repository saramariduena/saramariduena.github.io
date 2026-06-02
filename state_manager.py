"""
Gestiona el estado de sentencias ya procesadas para detectar novedades.
El estado se guarda en state.json (raíz del repositorio).
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent / "state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen_sentences": [], "last_run": "", "total_processed": 0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Estado guardado: {len(state.get('seen_sentences', []))} sentencias registradas")


def find_new_sentencias(current: list[dict], state: dict) -> list[dict]:
    """Retorna solo las sentencias que no habían sido vistas antes."""
    seen = set(state.get("seen_sentences", []))
    new_ones = [s for s in current if s.get("numero") and s["numero"] not in seen]
    return new_ones


def update_state(state: dict, new_sentencias: list[dict]) -> dict:
    seen = set(state.get("seen_sentences", []))
    for s in new_sentencias:
        if s.get("numero"):
            seen.add(s["numero"])
    state["seen_sentences"] = sorted(seen)
    state["last_run"] = datetime.now().isoformat()
    state["total_processed"] = len(seen)
    return state
