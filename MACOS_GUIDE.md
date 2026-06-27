# macOS Guide — From Zero to Your First Video

A complete, copy-paste walkthrough for macOS. No API keys, no accounts needed.
Total time: ~15 min setup (mostly waiting on installs), then a few minutes per video.

---

## Step 1 — Install Homebrew (skip if you already have it)
Homebrew is the standard macOS package installer. Open **Terminal**
(press `Cmd+Space`, type "Terminal", Enter) and paste:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After it finishes, if it tells you to run a couple `echo ... >> ~/.zprofile`
commands to "add Homebrew to your PATH", run them. Then close and reopen Terminal.

Check it works:
```bash
brew --version
```

---

## Step 2 — Install Python 3.11 and ffmpeg
```bash
brew install python@3.11 ffmpeg
```
Verify both:
```bash
python3.11 --version    # should print Python 3.11.x
ffmpeg -version         # should print ffmpeg version ...
```

---

## Step 3 — Download the project
```bash
cd ~/Desktop
git clone https://github.com/jarni66/short-video-pipeline.git
cd short-video-pipeline
```
(If `git` isn't installed, macOS will prompt to install the Command Line Tools —
accept it, then re-run the clone.)

---

## Step 4 — One-time setup
```bash
chmod +x setup.sh make_videos.sh
./setup.sh
```
This builds the Python environment and installs everything (a few minutes — lots
of scrolling is normal). It finishes with:
```
OK - ready. No API keys needed.
```
> If macOS says the script "cannot be opened" or is "from an unidentified
> developer", just run it with bash instead: `bash setup.sh`

---

## Step 5 — Make your first videos
The project comes with 3 example topics in `sample_concepts.json`. Generate them:
```bash
./make_videos.sh
```
You'll see it: write the voiceover → find & download background clips → add
subtitles → render. Each video takes ~5-10 minutes (it does 2 at a time).

When done, your finished videos are here:
```
short-video-pipeline/storage/tasks/<topic-name>/final-1.mp4
```
Open that folder in Finder:
```bash
open storage/tasks
```

---

## Step 6 — Make your own videos
Open `sample_concepts.json` in any text editor (or TextEdit) and replace the
examples. Each video concept needs:

```json
{
  "title": "How Volcanoes Erupt",
  "video_script": "Narration text the voice will read, about 130-150 words for a ~1 minute video...",
  "video_terms": ["volcano eruption", "lava flow", "magma", "volcanic ash"]
}
```
- **title** — the topic
- **video_script** — what the narrator says (~130-150 words ≈ 1 min)
- **video_terms** — a few English keywords used to find background footage

Set the narrator voice once at the top in `defaults.voice_name`
(e.g. `en-US-GuyNeural-Male`, `en-US-AriaNeural-Female`). Many languages exist.

Then run it on your file:
```bash
./make_videos.sh my_concepts.json
```

---

## Optional — visual dashboard instead of the command line
```bash
venv/bin/python -m streamlit run dashboard.py --server.port 8502
```
Then open **http://localhost:8502** in your browser: paste concepts JSON, click
**Generate pool**, and watch progress + logs live.

---

## Troubleshooting
| Problem | Fix |
|---|---|
| `python3.11: command not found` | `brew install python@3.11`, reopen Terminal |
| `ffmpeg: command not found` | `brew install ffmpeg` |
| `bad interpreter` / `permission denied` on a script | run `bash setup.sh` / `bash make_videos.sh` |
| A video fails to find footage | simplify that concept's `video_terms` to common words |
| YouTube briefly blocks downloads | just run `./make_videos.sh` again — it skips finished videos and retries the rest |
| Apple Silicon (M1/M2/M3) dependency install fails | ensure `which python3.11` is under `/opt/homebrew` (the arm64 Homebrew) |

## Notes
- **Fully key-free:** voiceover (Microsoft Edge TTS) and footage (yt-dlp) are
  free and need no accounts. There's no daily limit.
- **Footage license:** clips come from a general YouTube search (any license) —
  fine for personal use. If you plan to **publish & monetize**, swap in your own
  royalty-free footage to avoid copyright claims.
- **Music:** a random track from `resource/bgm` is mixed in — replace those
  `.mp3`s with your own if you want.
