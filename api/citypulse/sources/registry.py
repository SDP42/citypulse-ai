"""Source register loaded from data/source_register.json (single source of truth; no claims in UI code)."""
import json

from citypulse.core.settings import ROOT

REGISTER = ROOT / "data" / "source_register.json"
STATUSES = {"candidate", "verified", "research-only", "blocked", "disabled"}


def load_register() -> list[dict]:
    items = json.loads(REGISTER.read_text())
    for s in items:
        assert s["source_status"] in STATUSES, s["source_id"]
    return items
