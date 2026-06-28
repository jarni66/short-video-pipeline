# macOS — How to Generate a Video (Everyday Guide)

For when the project is **already installed** on this Mac. This covers normal
use: from turning the laptop on to a finished video. (Installation is only ever
done once — see `README_FRIEND.md` if you ever need to set it up again.)

> How to paste in Terminal: copy a command, click the Terminal window, press
> **Cmd+V**, then **Return**.

---

## Step 1 — Open the Terminal
1. Press **Cmd + Space**, type **Terminal**, press **Return**.

## Step 2 — Go into the project folder
```bash
cd ~/Desktop/short-video-pipeline
```
(That's where it was installed. If it's somewhere else, use that path instead.)

## Step 3 — Generate videos
To make the topics currently in the file:
```bash
./make_videos.sh
```
It runs through: voiceover → find & download footage → subtitles → render.
Each video takes ~5–10 minutes (2 at a time). It prints **"Done"** when finished.

## Step 4 — Find and play your video
```bash
open storage/tasks
```
Open a topic folder and double-click **`final-1.mp4`** to watch it. 🎉

---

## Making NEW videos (your own topics)
The videos come from a simple text file. To make different ones, change the topics:

1. Open the topics file:
   ```bash
   open -e sample_concepts.json
   ```
   (or open it in VS Code)
2. Replace/add topics. Each video is one block:
   ```json
   {
     "title": "How Volcanoes Erupt",
     "video_script": "Beneath the surface, magma builds up pressure until it bursts through... (about 130-150 words = ~1 minute)",
     "video_terms": ["volcano eruption", "lava flow", "magma", "volcanic ash"]
   }
   ```
   - **title** — the topic
   - **video_script** — exactly what the narrator says
   - **video_terms** — a few simple English keywords to find background clips
   Add as many blocks as the number of videos you want (separate with commas).
3. Save (**Cmd+S**), then run:
   ```bash
   ./make_videos.sh
   ```

**Tips**
- Write scripts with ChatGPT/Claude and paste them into `video_script`.
- Change the narrator voice at the top in `defaults.voice_name`
  (e.g. `en-US-GuyNeural-Male`, `en-US-AriaNeural-Female`).
- Keep your own topics in a separate file and run it by name:
  `./make_videos.sh my_videos.json`

---

## Optional — visual dashboard instead of commands
```bash
venv/bin/python -m streamlit run dashboard.py --server.port 8502
```
Open **http://localhost:8502** in a browser: paste concepts, click **Generate
pool**, watch progress. (Ignore the "Upload" buttons.) Press **Ctrl+C** to stop.

---

## Quick troubleshooting
| What you see | What to do |
|---|---|
| A video can't find footage | make that topic's `video_terms` simpler/more common |
| Download briefly blocked by YouTube | just run `./make_videos.sh` again — it skips finished videos and retries |
| "permission denied" running the script | run `bash make_videos.sh` instead |

## Notes
- Videos land in `storage/tasks/<topic>/final-1.mp4`.
- Footage comes from a general YouTube search (any license) — fine for personal
  use; for publishing/monetizing, swap in your own royalty-free footage.
- Background music is a random track from `resource/bgm` — replace those `.mp3`s
  to change it.
