# macOS Guide — From Powering On to Your First Video

A complete, beginner-friendly walkthrough. **No coding knowledge, no API keys,
no accounts needed.** Just follow each step in order and copy-paste the commands.

- One-time setup: ~15 minutes (mostly waiting for installs to finish)
- Each video after that: ~5–10 minutes

> How to "paste" in Terminal: copy a command here, click the Terminal window,
> press **Cmd+V**, then press **Return**. Many installs print lots of text — that
> scrolling is normal. Just wait until you get the prompt back.

---

## Part 1 — Turn on the Mac and open the Terminal
1. Power on the Mac and log in.
2. Press **Cmd + Space** (opens Spotlight search).
3. Type **Terminal** and press **Return**. A small window with text opens —
   this is where you'll paste commands.

---

## Part 2 — Install Homebrew (the installer for the tools)
Copy-paste this into Terminal and press Return:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
- It may ask for your **Mac login password** — type it (you won't see characters
  as you type; that's normal) and press Return.
- It may ask you to press **Return** to continue — do so.
- Takes a few minutes.

**Important:** when it finishes, it may print two lines starting with
`echo ... >> ~/.zprofile` and `eval ...`. If you see those, copy-paste and run
**both of those lines**, then **close and reopen Terminal** (Cmd+Q, then reopen
via Spotlight).

Check it worked:
```bash
brew --version
```
If it prints a version number, you're good.

---

## Part 3 — Install Python, ffmpeg, and git
Paste this single command (installs all three):
```bash
brew install python@3.11 ffmpeg git
```
Wait for it to finish (a few minutes). Then verify:
```bash
python3.11 --version
ffmpeg -version
git --version
```
Each should print a version. (If `python3.11` says "not found", run
`brew install python@3.11` again and reopen Terminal.)

---

## Part 4 — Download the project
```bash
cd ~/Desktop
git clone https://github.com/jarni66/short-video-pipeline.git
cd short-video-pipeline
```
This puts a folder called **short-video-pipeline** on your Desktop and moves you
into it. (The `cd` command means "go into this folder".)

---

## Part 5 — One-time setup
```bash
chmod +x setup.sh make_videos.sh
./setup.sh
```
`setup.sh` builds the project's environment and installs everything it needs
(a few minutes of scrolling text — normal). It's done when you see:
```
OK - ready. No API keys needed.
```
> If macOS blocks it with "cannot be opened" or "unidentified developer",
> run it this way instead: `bash setup.sh`

---

## Part 6 — Generate your first video
The project comes with 3 example topics. To make them:
```bash
./make_videos.sh
```
You'll watch it: create the voiceover → find & download background clips → add
subtitles → render the video. Each video takes ~5–10 minutes (it does 2 at once).

When it finishes it prints **"Done"**.

---

## Part 7 — Find and play your video
Open the output folder in Finder:
```bash
open storage/tasks
```
Inside you'll see a folder for each topic. Open one and double-click
**`final-1.mp4`** to play it.

🎉 That's your first video — made with no keys and no accounts.

---

## Part 8 — Make your OWN videos
The videos come from a simple text file. To make new ones, you give it new topics.

1. Open the project in a text editor. Easiest: in Terminal run
   ```bash
   open -e sample_concepts.json
   ```
   (or open the file in VS Code if you have it).
2. Replace the examples with your own. Each video is one block like this:
   ```json
   {
     "title": "How Volcanoes Erupt",
     "video_script": "Beneath the surface, molten rock called magma builds up pressure until it bursts through the crust... (write about 130-150 words, ~1 minute of narration)",
     "video_terms": ["volcano eruption", "lava flow", "magma", "volcanic ash"]
   }
   ```
   - **title** = the topic
   - **video_script** = exactly what the narrator says
   - **video_terms** = a few simple English keywords to find background footage
3. Add as many blocks as the number of videos you want (separate them with commas
   inside the `video_concepts` list). Save the file (**Cmd+S**).
4. Generate:
   ```bash
   ./make_videos.sh
   ```

**Tip:** you can write scripts with ChatGPT/Claude, then paste them into the
`video_script` fields. Change the narrator voice at the top in
`defaults.voice_name` (e.g. `en-US-AriaNeural-Female`).

---

## Part 9 (optional) — Use the visual dashboard instead of commands
```bash
venv/bin/python -m streamlit run dashboard.py --server.port 8502
```
Then open **http://localhost:8502** in your browser. Paste your concepts, click
**Generate pool**, and watch progress. (Ignore the "Upload" buttons — those need
extra accounts and aren't part of this setup.) Press **Ctrl+C** in Terminal to stop it.

---

## Coming back later (after closing everything)
You don't redo setup. Just:
```bash
cd ~/Desktop/short-video-pipeline
./make_videos.sh
```

---

## Troubleshooting
| What you see | What to do |
|---|---|
| `command not found: brew` | Finish Part 2's PATH lines, then reopen Terminal |
| `python3.11: command not found` | `brew install python@3.11`, reopen Terminal |
| `ffmpeg: command not found` | `brew install ffmpeg` |
| Script won't run / "permission denied" | run `bash setup.sh` and `bash make_videos.sh` |
| A video fails to find footage | make that topic's `video_terms` simpler/more common |
| Download briefly blocked by YouTube | just run `./make_videos.sh` again — it skips finished videos and retries |
| Apple Silicon (M1/M2/M3) install error | make sure `which python3.11` shows `/opt/homebrew/...` |

## Good to know
- **Fully free & key-free:** the voiceover (Microsoft Edge TTS) and footage
  (yt-dlp) need no accounts. No daily limits.
- **Footage license:** clips come from general YouTube search (any license) —
  fine for personal use/experimenting. If you'll **publish & monetize**, replace
  with your own royalty-free footage to avoid copyright claims.
- **Background music:** a random track from `resource/bgm` — swap in your own
  `.mp3`s anytime.
