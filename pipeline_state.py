"""
Shared state for the automated generate -> upload pipeline.

Single source of truth: .notes/pipeline_state.json

Each concept moves through statuses:
    pending  -> generated -> uploaded
                          \-> (failed at generate or upload)

Used by generate_pool.py, upload_next.py, and dashboard.py.
"""

import json
import os
import re
from datetime import datetime, timezone

from app.utils import utils

STATE_FILE = os.path.join(utils.root_dir(), ".notes", "pipeline_state.json")

# Generation settings (kept here so all entry points agree).
VOICE_NAME = "id-ID-ArdiNeural-Male"
FONT_SIZE = 30
SUBTITLE_POSITION = "custom"
CUSTOM_POSITION = 70.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:40]


def task_id_for(concept: dict) -> str:
    return f"howitworks-{concept['id']:02d}-{slugify(concept['title'])}"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"concepts": [], "defaults": {}, "updated_at": now_iso()}


def _norm_title(title: str) -> str:
    """Identity key for a concept (case/space-insensitive title)."""
    return re.sub(r"\s+", " ", (title or "").strip().casefold())


def clear_queue() -> dict:
    """Empty the queue (keeps the file). Use to start a fresh batch."""
    state = {"concepts": [], "defaults": {}, "updated_at": now_iso()}
    save_state(state)
    return state


def save_state(state: dict):
    state["updated_at"] = now_iso()
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _coerce_concepts(raw) -> list:
    """Accept either the full concepts.json object or a bare list."""
    if isinstance(raw, dict) and "video_concepts" in raw:
        return raw["video_concepts"]
    if isinstance(raw, list):
        return raw
    raise ValueError("Concepts JSON must be a list or have a 'video_concepts' key.")


OPTIONAL_FIELDS = ("youtube_title", "description", "video_terms", "tags", "hashtags", "thumbnail_prompt")


def load_concepts_into_state(raw, replace: bool = False) -> dict:
    """
    Merge a concepts JSON into the pipeline state.

    - Identity is the (normalized) title, NOT a user-supplied id. IDs are
      auto-assigned by the pipeline; any 'id' in the JSON is ignored.
    - Existing concepts (matched by title) keep their id + status/links so
      re-loading or appending never wipes progress; new titles are appended as
      'pending' with the next free id.
    - replace=True clears the queue first (fresh batch).
    - A top-level 'defaults' object (voice_name, video_source) is stored and
      used as fallback during generation.
    """
    concepts = _coerce_concepts(raw)
    state = clear_queue() if replace else load_state()
    if isinstance(raw, dict) and isinstance(raw.get("defaults"), dict):
        state["defaults"] = raw["defaults"]

    by_title = {_norm_title(c["title"]): c for c in state.get("concepts", [])}
    next_id = max([c.get("id", 0) for c in state.get("concepts", [])], default=0) + 1

    for c in concepts:
        title = (c.get("title") or "").strip()
        script = (c.get("video_script") or "").strip()
        if not title and not script:
            continue  # blank template slot — skip silently
        if not title or not script:
            raise ValueError(
                f"Concept '{title or '(untitled)'}' needs BOTH 'title' and 'video_script'."
            )
        key = _norm_title(c["title"])
        prev = by_title.get(key)
        if prev:
            # keep id + progress, refresh editable fields
            prev["video_script"] = c["video_script"]
            for f in OPTIONAL_FIELDS:
                if f in c:
                    prev[f] = c[f]
        else:
            entry = {
                "id": next_id,
                "title": c["title"],
                "status": "pending",
                "task_id": "",
                "video_path": "",
                "youtube_url": "",
                "generated_at": "",
                "uploaded_at": "",
                "error": "",
                "video_script": c["video_script"],
            }
            string_fields = ("youtube_title", "description", "thumbnail_prompt")
            for f in OPTIONAL_FIELDS:
                entry[f] = c.get(f, "" if f in string_fields else [])
            state["concepts"].append(entry)
            by_title[key] = entry
            next_id += 1

    save_state(state)
    return state


def update_concept(state: dict, cid: int, **fields) -> dict:
    for c in state["concepts"]:
        if c["id"] == cid:
            c.update(fields)
            break
    return state


def counts(state: dict) -> dict:
    out = {"pending": 0, "generated": 0, "uploaded": 0, "failed": 0, "total": 0}
    for c in state.get("concepts", []):
        out["total"] += 1
        out[c.get("status", "pending")] = out.get(c.get("status", "pending"), 0) + 1
    return out


def pending_to_generate(state: dict) -> list:
    return [c for c in state["concepts"] if c.get("status") in ("pending", "failed")
            and c.get("status") != "uploaded" and not c.get("video_path")]


def ready_to_upload(state: dict) -> list:
    """Generated-but-not-uploaded, oldest first."""
    ready = [c for c in state["concepts"] if c.get("status") == "generated"]
    ready.sort(key=lambda c: c.get("generated_at", ""))
    return ready
