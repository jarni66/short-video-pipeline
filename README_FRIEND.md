# Auto Video Maker — Generate-Only, No API Keys Needed

Makes short narrated videos automatically: you give it a topic + script, it
generates an AI voiceover, finds matching background footage from YouTube, adds
subtitles, and stitches a finished MP4 — **with no API keys to sign up for.**

---

## macOS setup

### 1. Install the two requirements (one time)
Open **Terminal** and, if you don't have Homebrew, install it from https://brew.sh
Then:
```bash
brew install python@3.11 ffmpeg
```

### 2. Get the project
```bash
git clone https://github.com/jarni66/short-video-pipeline.git
cd short-video-pipeline
```

### 3. Set up (one time)
```bash
chmod +x setup.sh make_videos.sh
./setup.sh
```
It builds the environment and ends with "OK - ready. No API keys needed."

### 4. Make videos
```bash
./make_videos.sh                 # uses sample_concepts.json
# or your own file:
./make_videos.sh my_concepts.json
```
Finished videos appear in: `storage/tasks/<topic-name>/final-1.mp4`

> If macOS blocks the script ("cannot be opened"), run `bash setup.sh` instead.

---

## Windows setup (alternative)
1. Install **Python 3.11** (tick "Add to PATH") and **ffmpeg** (`winget install Gyan.FFmpeg`).
2. `git clone https://github.com/jarni66/short-video-pipeline.git`
3. Double-click **`setup.bat`**, then **`make_videos.bat`**.

---

## Writing your own videos
Edit **`sample_concepts.json`** (or make your own). Each concept needs:
- `title` — the topic
- `video_script` — narration text (~130-150 words ≈ 1 minute)
- `video_terms` — a few English keywords to find background footage

Set the voice per batch in `defaults.voice_name`, e.g. `en-US-GuyNeural-Male`,
`en-US-AriaNeural-Female`, `id-ID-ArdiNeural-Male` (many languages available).

## Optional dashboard (UI instead of the script)
```bash
venv/bin/python -m streamlit run dashboard.py --server.port 8502   # macOS
```
Then open http://localhost:8502 — paste concepts, click Generate, watch progress.

## Good to know
- **No accounts or API keys** to generate. Voiceover (Edge TTS) and footage
  (yt-dlp) are free and keyless. No daily limits.
- **Footage license:** clips come from a general YouTube search (any license) —
  fine for personal use/experimenting. If you plan to **publish & monetize**,
  swap in your own licensed/royalty-free footage to avoid copyright claims.
- **Background music:** random track from `resource/bgm` — replace with your own
  `.mp3`s if you like.
- **Speed:** ~5-10 min per video (2 at a time); faster CPU helps.

## Troubleshooting
- `python3.11: command not found` → `brew install python@3.11`, reopen Terminal.
- `ffmpeg not found` → `brew install ffmpeg`.
- A video can't find footage → simplify that concept's `video_terms`.
- YouTube briefly blocks downloads → just run `./make_videos.sh` again; it skips
  finished ones and retries the rest.
- Apple Silicon (M1/M2/M3): if a dependency fails to install, make sure you're
  using the arm64 Homebrew Python (`which python3.11` should be under
  `/opt/homebrew`).
