# Batch Seed JSON — Full Schema

The concepts JSON you paste/upload in the dashboard (or load via `pipeline_state`).

## Top-level object

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `channel` | string | no | — | Metadata only (not consumed by the pipeline). |
| `language` | string | no | — | Metadata only. |
| `defaults` | object | no | `{}` | Batch-wide fallbacks (see below). |
| `video_concepts` | array | **yes** | — | The list of concepts. May also be passed as a bare top-level array. |

## `defaults` object (batch-wide fallbacks)

| Field | Type | Default | Notes |
|---|---|---|---|
| `voice_name` | string | `id-ID-ArdiNeural-Male` | Any edge-tts voice, e.g. `id-ID-GadisNeural-Female`. |
| `video_source` | string | `youtube` | One of `youtube`, `pexels`, `pixabay`, `coverr`, `local`. Env `MPT_VIDEO_SOURCE` overrides. |

## Each item in `video_concepts`

| Field | Type | Required | Default | Used for |
|---|---|---|---|---|
| `title` | string | **yes** | — | Generation subject + fallback YouTube title. **Also the identity key** (dedup/merge across loads). |
| `video_script` | string | **yes** | — | TTS narration. Target ~130–150 words (~1 min). |
| `youtube_title` | string | no | `""` | Published title. ≤100 chars (truncated). Falls back to `title` if empty. |
| `description` | string | no | `""` | YouTube description. ≤5000 chars (truncated). Hashtags appended automatically. |
| `video_terms` | string[] | no | `[]` | Manual footage search keywords (English). **Empty → Gemini auto-generates** 5 from the script. |
| `tags` | string[] | no | `[]` | YouTube SEO tags. Empty → a generic default set. |
| `hashtags` | string[] | no | `[]` | Appended to the description. Empty → `#HowThingsWork #Edukasi #Sains`. |
| `thumbnail_prompt` | string | no | `""` | Image prompt for the AI thumbnail (always add "no text"). **Empty → auto-built** from `title` + `description`. |
| `id` | int | no | — | **Ignored.** IDs are auto-assigned by the pipeline. |

## Auto-managed fields (added by the pipeline, never in the seed)
`id`, `status` (`pending`→`generated`→`uploaded`/`failed`), `task_id`, `video_path`,
`youtube_url`, `generated_at`, `uploaded_at`, `thumbnail_path`, `error`.

## Behavior rules
- **Identity = title** (normalized). Re-loading the same title keeps its progress; a new title is appended. Duplicate titles merge into one.
- **Blank slots** (both `title` and `video_script` empty) are skipped silently — fill only the slots you need.
- A half-filled slot (one of `title`/`video_script` present, the other empty) is rejected with an error.
- **Append vs Replace**: dashboard "Replace queue" clears first; otherwise it merges.

## NOT in the seed — these live in `config.toml`
- `youtube_upload_privacy` (`private`/`unlisted`/`public`)
- `youtube_video_license` (`creativeCommon`/`any`), `youtube_video_duration`, `youtube_max_results`, `youtube_max_height`
- `youtube_thumbnail_enabled`, `thumbnail_model`, `thumbnail_text_overlay`
- Upload schedule (2/day) is in Windows Task Scheduler, not the JSON.

## Minimal valid example
```json
{ "video_concepts": [ { "title": "Cara Kerja Resleting", "video_script": "Resleting mungkin benda..." } ] }
```

## Full example (one concept, all fields)
```json
{
  "channel": "How Things Work",
  "language": "Indonesia",
  "defaults": { "voice_name": "id-ID-ArdiNeural-Male", "video_source": "youtube" },
  "video_concepts": [
    {
      "title": "Cara Kerja Microwave Memanaskan Makanan",
      "youtube_title": "Microwave TIDAK Memasak dari Dalam ke Luar?! 🤯",
      "description": "Membongkar mitos microwave dan menjelaskan bagaimana gelombang menggetarkan molekul air.",
      "video_terms": ["microwave oven", "water molecules vibrating", "metal sparks microwave"],
      "tags": ["cara kerja", "microwave", "sains", "edukasi"],
      "hashtags": ["#CaraKerja", "#Sains", "#Edukasi"],
      "thumbnail_prompt": "glowing microwave, electromagnetic waves, water molecules, dramatic blue-orange lighting, no text",
      "video_script": "Kamu mungkin pernah dengar microwave memasak makanan dari dalam ke luar. Itu salah! ..."
    }
  ]
}
```
