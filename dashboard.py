"""
Control dashboard for the automated generate -> upload pipeline.

Run with:
    venv\\Scripts\\python.exe -m streamlit run dashboard.py --server.port 8502

Features:
  - live queue table (pending / generated / uploaded) with YouTube links
  - paste a concepts JSON to (re)load the queue
  - start batch generation (fills the pool, parallel-2)
  - upload the next 1 or 2 ready videos now
  - tail the generation / upload logs
"""

import json
import os
import subprocess

import streamlit as st

from app.config import config
from app.utils import utils
import pipeline_state as ps

ROOT = utils.root_dir()
# cross-platform venv python: Windows uses venv\Scripts\python.exe, macOS/Linux uses venv/bin/python
_VENV_BIN = "Scripts" if os.name == "nt" else "bin"
_VENV_EXE = "python.exe" if os.name == "nt" else "python"
PYTHON = os.path.join(ROOT, "venv", _VENV_BIN, _VENV_EXE)
GEN_LOG = os.path.join(ROOT, "storage", "generate_pool.log")
UPLOAD_LOG = os.path.join(ROOT, "storage", "upload.log")

st.set_page_config(page_title="MoneyPrinterTurbo Pipeline", layout="wide")


def launch(args, logfile):
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    env = dict(os.environ, MPT_VIDEO_SOURCE="youtube")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(f"\n==== launch {' '.join(args)} ====\n")
        f.flush()
        subprocess.Popen(
            [PYTHON, *args],
            cwd=ROOT,
            stdout=f,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )


def tail(path, n=30) -> str:
    if not os.path.exists(path):
        return "(no log yet)"
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-n:]) or "(empty)"


# ----------------------------------------------------------------------------
st.title("🎬 MoneyPrinterTurbo — Pipeline Dashboard")

state = ps.load_state()
c = ps.counts(state)

m = st.columns(5)
m[0].metric("Total", c["total"])
m[1].metric("Pending", c["pending"])
m[2].metric("Generated", c["generated"])
m[3].metric("Uploaded", c["uploaded"])
m[4].metric("Failed", c["failed"])

priv = config.app.get("youtube_upload_privacy", "private")
st.caption(
    f"Footage: **{config.app.get('youtube_video_license')}** · "
    f"Upload privacy: **{priv}** · Source: **youtube** · "
    f"Schedule: 2/day (morning + evening) via Task Scheduler"
)

# ---- Controls --------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
if col1.button("▶ Generate pool (all pending)", use_container_width=True):
    launch(["generate_pool.py"], GEN_LOG)
    st.success("Generation started in the background. Watch the log below.")
if col2.button("⬆ Upload next 1", use_container_width=True):
    launch(["upload_next.py", "1"], UPLOAD_LOG)
    st.success("Upload (1) started. Watch the log below.")
if col3.button("⬆ Upload next 2", use_container_width=True):
    launch(["upload_next.py", "2"], UPLOAD_LOG)
    st.success("Upload (2) started. Watch the log below.")
if col4.button("🔄 Refresh", use_container_width=True):
    st.rerun()

# ---- Load concepts JSON ----------------------------------------------------
PLACEHOLDER = (
    '{\n'
    '  "channel": "How Things Work",\n'
    '  "defaults": { "voice_name": "id-ID-ArdiNeural-Male", "video_source": "youtube" },\n'
    '  "video_concepts": [\n'
    '    {\n'
    '      "title": "Cara Kerja Microwave Memanaskan Makanan",\n'
    '      "youtube_title": "Microwave TIDAK Memasak dari Dalam?! \U0001f92f",\n'
    '      "description": "Membongkar mitos microwave...",\n'
    '      "video_terms": ["microwave oven", "water molecules vibrating", "metal sparks"],\n'
    '      "tags": ["cara kerja", "microwave", "sains"],\n'
    '      "hashtags": ["#CaraKerja", "#Sains"],\n'
    '      "thumbnail_prompt": "glowing microwave, electromagnetic waves, water molecules, dramatic lighting, no text",\n'
    '      "video_script": "Kamu mungkin pernah dengar..."\n'
    '    }\n'
    '  ]\n'
    '}'
)


def validate_concepts(raw) -> list:
    """Return a list of human-readable warnings (empty = all good)."""
    warns = []
    concepts = raw.get("video_concepts", raw) if isinstance(raw, dict) else raw
    if not isinstance(concepts, list) or not concepts:
        return ["No 'video_concepts' array found."]
    seen = set()
    for i, c in enumerate(concepts, 1):
        t = (c.get("title") or "").strip()
        s = (c.get("video_script") or "").strip()
        if not t and not s:
            continue  # blank template slot — ignored on load
        if not t:
            warns.append(f"#{i}: has a script but missing 'title'.")
        if not s:
            warns.append(f"#{i} ({t or '?'}): missing 'video_script'.")
        if t.casefold() in seen:
            warns.append(f"#{i}: duplicate title '{t}' (will merge into one).")
        seen.add(t.casefold())
        yt = c.get("youtube_title") or t
        if len(yt) > 100:
            warns.append(f"#{i} ({t}): youtube_title is {len(yt)} chars (>100, will be truncated).")
    return warns


with st.expander("➕ Load concepts (paste your concepts JSON — no 'id' needed)"):
    st.caption("IDs are auto-assigned. Concepts are matched by title, so re-loading keeps progress.")
    txt = st.text_area("Concepts JSON", height=240, placeholder=PLACEHOLDER)
    up = st.file_uploader("…or upload a .json file", type=["json"])
    replace = st.checkbox("Replace queue (clear existing first)", value=False)
    cval, cclear = st.columns([3, 1])
    if cval.button("Load into queue", use_container_width=True):
        try:
            raw = json.loads(up.read().decode("utf-8")) if up else json.loads(txt)
            warns = validate_concepts(raw)
            for w in warns:
                st.warning(w)
            blocking = [w for w in warns if "missing" in w or "No 'video_concepts'" in w]
            if blocking:
                st.error("Fix the missing required fields above before loading.")
            else:
                new_state = ps.load_concepts_into_state(raw, replace=replace)
                st.success(f"Queue now has {len(new_state['concepts'])} concepts.")
                st.rerun()
        except Exception as e:
            st.error(f"Could not parse concepts JSON: {e}")
    if cclear.button("🗑 Clear queue", use_container_width=True):
        ps.clear_queue()
        st.rerun()

# ---- Queue table -----------------------------------------------------------
st.subheader("Queue")
if state.get("concepts"):
    rows = []
    for x in state["concepts"]:
        rows.append(
            {
                "id": x["id"],
                "title": x["title"],
                "status": x.get("status", "pending"),
                "youtube": x.get("youtube_url", ""),
                "uploaded_at": x.get("uploaded_at", ""),
                "error": x.get("error", ""),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("Queue is empty. Load a concepts JSON above to get started.")

# ---- Logs ------------------------------------------------------------------
lc1, lc2 = st.columns(2)
with lc1:
    st.subheader("Generation log")
    st.code(tail(GEN_LOG), language="log")
with lc2:
    st.subheader("Upload log")
    st.code(tail(UPLOAD_LOG), language="log")
