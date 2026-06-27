"""
Upload the next N generated-but-not-uploaded videos to YouTube (oldest first).

Triggered by Windows Task Scheduler twice a day (1 each) for 2 uploads/day.
Privacy comes from config.toml (youtube_upload_privacy). Auth is OAuth as the
channel owner (see youtube_upload.py setup).

Usage:
    venv\\Scripts\\python.exe upload_next.py        # upload 1 (default)
    venv\\Scripts\\python.exe upload_next.py 2      # upload 2
"""

import sys

from loguru import logger

from app.config import config

import pipeline_state as ps
import thumbnail
import youtube_upload


def build_description(concept: dict) -> str:
    # CC-BY footage requires attribution; per-clip credits can't be auto-collected.
    hashtags = concept.get("hashtags") or ["#HowThingsWork", "#Edukasi", "#Sains"]
    if isinstance(hashtags, list):
        hashtags = " ".join(hashtags)
    return (
        f"{concept.get('description', '')}\n\n"
        f"{hashtags}\n\n"
        f"Footage: Creative Commons licensed clips via YouTube."
    )


def build_tiktok_caption(concept: dict) -> str:
    """TikTok caption: title + hashtags (TikTok favours hashtags for reach)."""
    title = concept.get("youtube_title") or concept["title"]
    tags = concept.get("hashtags") or ["#CaraKerja", "#Sains", "#Edukasi"]
    if isinstance(tags, list):
        tags = " ".join(tags)
    # add a couple of TikTok-discovery tags (ASCII-safe)
    return f"{title}\n\n{tags} #fyp #foryou"[:2200]


def cross_post_tiktok(concept: dict, state: dict, cid: int):
    """Optionally cross-post the same video to TikTok via upload-post.com."""
    from app.services.upload_post import UploadPostService

    svc = UploadPostService()
    if not svc.is_configured():
        return  # not enabled / not configured — silent no-op
    privacy = config.app.get("upload_post_privacy", "SELF_ONLY")
    logger.info(f"[concept {cid}] cross-posting to TikTok ({privacy})")
    tk = svc.upload_video(
        video_path=concept["video_path"],
        title=build_tiktok_caption(concept),
        platforms=["tiktok"],
        privacy_level=privacy,
    )
    if tk.get("success"):
        logger.success(f"[concept {cid}] TikTok ok (req {tk.get('request_id')})")
        ps.update_concept(state, cid, tiktok_status="posted",
                          tiktok_request_id=str(tk.get("request_id", "")))
    else:
        logger.warning(f"[concept {cid}] TikTok failed: {tk.get('error') or tk.get('message')}")
        ps.update_concept(state, cid, tiktok_status="failed")
    ps.save_state(state)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1

    state = ps.load_state()
    ready = ps.ready_to_upload(state)
    if not ready:
        logger.success("No videos ready to upload.")
        return

    to_upload = ready[:n]
    logger.info(f"uploading {len(to_upload)} video(s) of {len(ready)} ready")

    uploaded = 0
    for concept in to_upload:
        cid = concept["id"]
        logger.info(f"[concept {cid}] uploading: {concept['title']}")
        result = youtube_upload.upload_video(
            video_path=concept["video_path"],
            title=concept.get("youtube_title") or concept["title"],
            description=build_description(concept),
            tags=concept.get("tags") or ["how things work", "edukasi", "sains", "cara kerja", "science"],
        )
        state = ps.load_state()  # reload in case dashboard changed it
        if result.get("success"):
            video_id = result["video_id"]
            thumb_url = ""
            # optional AI thumbnail (no-op/clear warning if channel unverified)
            if config.app.get("youtube_thumbnail_enabled", True):
                thumb_path = thumbnail.generate_thumbnail(concept)
                if thumb_path:
                    tr = youtube_upload.set_thumbnail(video_id, thumb_path)
                    thumb_url = thumb_path if tr.get("success") else ""
            ps.update_concept(
                state, cid, status="uploaded",
                youtube_url=result["url"], uploaded_at=ps.now_iso(),
                thumbnail_path=thumb_url, error="",
            )
            ps.save_state(state)
            uploaded += 1
            logger.success(f"[concept {cid}] uploaded -> {result['url']}")
            # optional: also push to TikTok via upload-post.com
            try:
                cross_post_tiktok(concept, ps.load_state(), cid)
            except Exception as e:
                logger.warning(f"[concept {cid}] TikTok cross-post error: {e}")
        else:
            ps.update_concept(state, cid, error=f"upload: {result.get('error')}")
            ps.save_state(state)
            logger.error(f"[concept {cid}] upload failed: {result.get('error')}")
            # stop on failure (likely quota/auth) rather than burn through the pool
            sys.exit(1)

    logger.success(f"uploaded {uploaded} video(s). Pool: {ps.counts(ps.load_state())}")


if __name__ == "__main__":
    main()
