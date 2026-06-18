"""Render caption cards as transparent PNGs (overlaid on the video).

PIL is used instead of ffmpeg drawtext (which crashes on some multi-line text /
fonts). Fonts are optional: pass paths via config, otherwise a scalable default
font is used — nothing is hardcoded to a particular OS.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

# orient: (width, height, impact_font_size, sub_font_size)
SPEC = {"short": (720, 1280, 64, 24), "long": (1280, 720, 52, 24)}


def load_font(size: int, path: str | None = None, index: int = 0):
    """A font at ``size``. Falls back to PIL's scalable default when no path."""
    if path:
        return ImageFont.truetype(path, size, index=index)
    try:
        return ImageFont.load_default(size)  # Pillow >= 10.1 (scalable)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def _line_h(font):
    ascent, descent = font.getmetrics()
    return ascent + descent


def _text(draw, x, y, text, font, alpha=240):
    """Drop shadow + white text, centered (anchor=ma)."""
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 200), anchor="ma")
    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha), anchor="ma")


def render_impact(impact: str, subtitle: str, orient: str, out_png: str,
                  font_impact: str | None = None, font_sub: str | None = None) -> str:
    """Big impact line(s) centered + a small subtitle near the bottom → card.

    ``impact`` may contain ``\\n`` for forced breaks; long lines wrap to width.
    """
    w, h, impact_fs, sub_fs = SPEC[orient]
    fi = load_font(impact_fs, font_impact)
    fs = load_font(sub_fs, font_sub)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    max_w = int(w * 0.82)

    lines = []
    for segment in impact.split("\n"):
        lines += _wrap(draw, segment.strip(), fi, max_w) if segment.strip() else [""]

    block_h = sum(_line_h(fi) + 8 for _ in lines)
    cy = (h - block_h) // 2
    for line in lines:
        _text(draw, w // 2, cy, line, fi)
        cy += _line_h(fi) + 8

    if subtitle:
        _text(draw, w // 2, int(h * 0.86), subtitle, fs, alpha=200)
    img.save(out_png)
    return out_png
