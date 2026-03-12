from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_MAX_GUIDS = 500


def load_state(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def save_state(path: str | Path, state: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(state, f, indent=2)


def is_seeded(state: dict, url: str) -> bool:
    return state.get(url, {}).get("seeded", False)


def seen_guids(state: dict, url: str) -> set[str]:
    return set(state.get(url, {}).get("seen_guids", []))


def mark_seen(state: dict, url: str, guids: list[str], seeded: bool = False) -> None:
    entry = state.setdefault(url, {"seen_guids": [], "last_run": None, "seeded": False})
    existing = entry["seen_guids"]
    new_guids = [g for g in guids if g not in set(existing)]
    existing.extend(new_guids)
    # FIFO eviction — keep the most recent _MAX_GUIDS
    if len(existing) > _MAX_GUIDS:
        entry["seen_guids"] = existing[-_MAX_GUIDS:]
    else:
        entry["seen_guids"] = existing
    entry["last_run"] = datetime.now(timezone.utc).isoformat()
    if seeded:
        entry["seeded"] = True
