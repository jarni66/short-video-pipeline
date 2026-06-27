"""
Generate all pending concepts into the video pool (parallel-2).

Reads the queue from pipeline_state.json, generates every concept still
'pending'/'failed', and marks each 'generated' with its video path. Upload is
a separate stage (upload_next.py) — this only fills the pool.

Usage:
    venv\\Scripts\\python.exe generate_pool.py            # generate all pending
    venv\\Scripts\\python.exe generate_pool.py --max 14   # cap how many this run
"""

import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from app.models.schema import VideoParams
from app.services import state as sm
from app.services import task as tm

import pipeline_state as ps

MAX_PARALLEL = 2


def build_params(concept: dict, defaults: dict) -> VideoParams:
    # precedence: per-concept > batch defaults > env > hardcoded default
    source = (
        defaults.get("video_source")
        or os.environ.get("MPT_VIDEO_SOURCE")
        or "youtube"
    )
    voice = defaults.get("voice_name") or ps.VOICE_NAME
    # optional manual footage keywords; None lets the LLM derive them
    terms = concept.get("video_terms") or None
    return VideoParams(
        video_subject=concept["title"],
        video_script=concept["video_script"],
        video_terms=terms,
        video_source=source,
        voice_name=voice,
        subtitle_enabled=True,
        subtitle_position=ps.SUBTITLE_POSITION,
        custom_position=ps.CUSTOM_POSITION,
        font_size=ps.FONT_SIZE,
    )


def generate_one(concept: dict, defaults: dict) -> dict:
    cid = concept["id"]
    task_id = ps.task_id_for(concept)
    logger.info(f"[concept {cid}] generating task_id={task_id}")
    try:
        sm.state.update_task(task_id)
        result = tm.start(task_id=task_id, params=build_params(concept, defaults), stop_at="video")
        videos = (result or {}).get("videos", []) if isinstance(result, dict) else []
        if not videos:
            raise RuntimeError("no video produced")
        return {"id": cid, "task_id": task_id, "ok": True, "video_path": videos[0]}
    except Exception as e:
        logger.error(f"[concept {cid}] FAILED: {e}\n{traceback.format_exc()}")
        return {"id": cid, "task_id": task_id, "ok": False, "error": str(e)}


def main():
    cap = None
    if "--max" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--max") + 1])

    state = ps.load_state()
    defaults = state.get("defaults", {})
    todo = ps.pending_to_generate(state)
    if cap:
        todo = todo[:cap]
    if not todo:
        logger.success("Nothing to generate — pool is full.")
        return

    source = defaults.get("video_source") or os.environ.get("MPT_VIDEO_SOURCE") or "youtube"
    logger.info(f"generating {len(todo)} concept(s) | parallel={MAX_PARALLEL} | source={source}")

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(generate_one, c, defaults): c["id"] for c in todo}
        for fut in as_completed(futures):
            r = fut.result()
            # reload+save per result so a crash mid-batch keeps finished work
            state = ps.load_state()
            if r["ok"]:
                ps.update_concept(
                    state, r["id"], status="generated", task_id=r["task_id"],
                    video_path=r["video_path"], generated_at=ps.now_iso(), error="",
                )
                logger.success(f"[concept {r['id']}] generated -> {r['video_path']}")
            else:
                ps.update_concept(state, r["id"], status="failed", error=r["error"])
            ps.save_state(state)

    final = ps.counts(ps.load_state())
    logger.success(f"pool status: {final}")


if __name__ == "__main__":
    main()
