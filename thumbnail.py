"""
AI thumbnail generator.

Generates a 9:16 background with Google Imagen (via the Gemini API key) and
overlays the title text crisply with PIL — because image models render text as
gibberish, so we draw legible text ourselves.

Returns a JPG path ready for youtube_upload.set_thumbnail().
"""

import base64
import os
import textwrap

import requests
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from app.config import config
from app.utils import utils

THUMB_DIR = os.path.join(utils.root_dir(), "storage", "thumbnails")
FONT_PATH = os.path.join(utils.root_dir(), "resource", "fonts", "MicrosoftYaHeiBold.ttc")

# Final thumbnail size — strictly 9:16, comfortably under YouTube's 2MB JPG limit.
OUT_W, OUT_H = 720, 1280
ASPECT_RATIO = "9:16"  # strict per requirement


def _image_model() -> str:
    return config.app.get("thumbnail_model", "gemini-2.5-flash-image")


def build_prompt(concept: dict) -> str:
    if concept.get("thumbnail_prompt"):
        return concept["thumbnail_prompt"]
    subject = concept.get("title", "")
    desc = concept.get("description", "")
    return (
        f"Eye-catching, high-contrast YouTube thumbnail background about: {subject}. "
        f"{desc} Bold dramatic cinematic lighting, vivid saturated colors, clear "
        f"central subject, simple uncluttered composition, vertical 9:16. "
        f"Absolutely no text, no letters, no words in the image."
    )


def _generate_background(prompt: str) -> Image.Image:
    """
    Generate a 9:16 background. Uses the Gemini native image model with
    imageConfig.aspectRatio (same approach as the content_pipeline project);
    Imagen models are supported as a fallback via the :predict endpoint.
    """
    key = config.app.get("gemini_api_key")
    if not key:
        raise ValueError("gemini_api_key not set — needed for AI thumbnails.")
    model = _image_model()

    if model.startswith("imagen"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={key}"
        body = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": ASPECT_RATIO},
        }
        resp = requests.post(url, json=body, timeout=120).json()
        preds = resp.get("predictions", [])
        if not preds or not preds[0].get("bytesBase64Encoded"):
            raise RuntimeError(f"imagen returned no image: {str(resp)[:300]}")
        raw = base64.b64decode(preds[0]["bytesBase64Encoded"])
    else:
        # Gemini native image model — aspect ratio goes in generationConfig.imageConfig
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": ASPECT_RATIO},
            },
        }
        resp = requests.post(url, json=body, timeout=120).json()
        raw = None
        for part in resp.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                raw = base64.b64decode(part["inlineData"]["data"])
                break
        if raw is None:
            raise RuntimeError(f"image model returned no image: {str(resp)[:300]}")

    tmp = os.path.join(THUMB_DIR, "_bg_raw")
    os.makedirs(THUMB_DIR, exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(raw)
    img = Image.open(tmp).convert("RGB")
    os.remove(tmp)
    return img


def _fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize+center-crop to exactly w x h (cover)."""
    src_ratio = img.width / img.height
    dst_ratio = w / h
    if src_ratio > dst_ratio:
        new_h = h
        new_w = int(h * src_ratio)
    else:
        new_w = w
        new_h = int(w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def _draw_title(img: Image.Image, title: str) -> Image.Image:
    """Overlay wrapped, outlined title text in the lower third."""
    if not config.app.get("thumbnail_text_overlay", True) or not title:
        return img
    draw = ImageDraw.Draw(img)
    margin = 40
    max_w = OUT_W - 2 * margin

    def wrap_px(words, font):
        """Greedy word-wrap by measured pixel width."""
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=font) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # shrink font until every line fits AND we have at most 4 lines
    words = title.upper().split()
    font, lines, font_size = None, None, None
    for fs in range(88, 36, -4):
        try:
            f = ImageFont.truetype(FONT_PATH, fs)
        except Exception:
            f = ImageFont.load_default()
        ls = wrap_px(words, f)
        widest = max(draw.textlength(l, font=f) for l in ls)
        if widest <= max_w and len(ls) <= 4:
            font, lines, font_size = f, ls, fs
            break
    if font is None:  # extreme fallback
        font, lines, font_size = f, ls, fs
    line_h = font_size + 14
    total_h = line_h * len(lines)
    y = OUT_H - total_h - 90  # lower third, with bottom margin

    # darken a band behind the text for legibility
    band_top = max(0, y - 30)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, band_top, OUT_W, OUT_H], fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    for line in lines:
        tw = draw.textlength(line, font=font)
        x = (OUT_W - tw) // 2
        # thick black outline
        for dx in (-3, -2, 0, 2, 3):
            for dy in (-3, -2, 0, 2, 3):
                draw.text((x + dx, y + dy), line, font=font, fill="black")
        draw.text((x, y), line, font=font, fill="#FFE600")  # bright yellow
        y += line_h
    return img


def generate_thumbnail(concept: dict, out_path: str = None) -> str:
    """Generate a thumbnail JPG for a concept. Returns the file path or ''."""
    title = concept.get("youtube_title") or concept.get("title", "")
    out_path = out_path or os.path.join(
        THUMB_DIR, f"{concept.get('id', 'x')}-thumb.jpg"
    )
    os.makedirs(THUMB_DIR, exist_ok=True)
    try:
        logger.info(f"generating thumbnail for: {title}")
        bg = _generate_background(build_prompt(concept))
        bg = _fit_cover(bg, OUT_W, OUT_H)
        bg = _draw_title(bg, title)
        # save as JPG, dial quality down if needed to stay under 2MB
        q = 90
        bg.save(out_path, "JPEG", quality=q)
        while os.path.getsize(out_path) > 2_000_000 and q > 50:
            q -= 10
            bg.save(out_path, "JPEG", quality=q)
        logger.success(f"thumbnail saved: {out_path} ({os.path.getsize(out_path)//1024} KB)")
        return out_path
    except Exception as e:
        logger.error(f"thumbnail generation failed: {e}")
        return ""


if __name__ == "__main__":
    import sys

    demo = {
        "id": "demo",
        "title": sys.argv[1] if len(sys.argv) > 1 else "Cara Kerja Microwave Memanaskan Makanan",
        "description": "Bagaimana gelombang mikro menggetarkan molekul air sampai panas.",
    }
    print(generate_thumbnail(demo))
