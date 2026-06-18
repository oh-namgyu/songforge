"""Video rendering — background + caption card(s) + audio → mp4.

Short = 720x1280 (9:16), long = 1280x720 (16:9), fixed 25fps. ``ff`` is the
ffmpeg binary path (from config). Background is a square clip so either crop
works; see background.py for the no-Pexels fallback.
"""
from __future__ import annotations

import os
import re
import subprocess

SIZES = {"short": (720, 1280), "long": (1280, 720)}


def duration(audio: str, ff: str) -> float:
    err = subprocess.run([ff, "-i", audio], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", err)
    if not m:
        raise RuntimeError(f"could not read duration of {audio}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def _cover(w: int, h: int) -> str:
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"


def lyric_video(audio: str, bg_video: str, card_png: str, out_mp4: str, ff: str,
                orient: str = "short") -> str:
    """Looped background + one card overlay + audio → mp4 (whole-song length)."""
    w, h = SIZES[orient]
    dur = duration(audio, ff)
    fc = (f"[0:v]{_cover(w, h)},eq=brightness=-0.10:saturation=0.95[bg];"
          "[bg][2:v]overlay=0:0,format=yuv420p[v]")
    part = out_mp4 + ".part.mp4"
    subprocess.run([
        ff, "-y", "-stream_loop", "-1", "-i", bg_video, "-i", audio, "-i", card_png,
        "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-r", "25",
        "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", part,
    ], check=True, capture_output=True)
    os.replace(part, out_mp4)  # atomic — no truncated mp4 if ffmpeg is killed
    return out_mp4


def teaser_video(audio: str, bg_video: str, lyric_png: str, end_png: str,
                 out_mp4: str, ff: str, orient: str = "short", switch: float = 14.0) -> str:
    """Background + (lyric card → fade → end card) + audio → teaser mp4.

    ``switch`` is when the lyric card fades out; the end card fades in just after
    and holds to the end.
    """
    w, h = SIZES[orient]
    dur = duration(audio, ff)
    switch = min(switch, max(dur - 1.5, 0.5))  # keep the card fades inside short audio
    fc = (f"[0:v]{_cover(w, h)},eq=brightness=-0.10:saturation=0.95[bg];"
          f"[2:v]format=yuva420p,fade=t=out:st={switch:.1f}:d=0.8:alpha=1[lc];"
          f"[3:v]format=yuva420p,fade=t=in:st={switch + 0.6:.1f}:d=0.8:alpha=1[ec];"
          "[bg][lc]overlay=0:0[t1];[t1][ec]overlay=0:0,format=yuv420p[v]")
    part = out_mp4 + ".part.mp4"
    subprocess.run([
        ff, "-y", "-stream_loop", "-1", "-i", bg_video, "-i", audio,
        "-loop", "1", "-framerate", "25", "-i", lyric_png,
        "-loop", "1", "-framerate", "25", "-i", end_png,
        "-filter_complex", fc, "-map", "[v]", "-map", "1:a",
        "-r", "25", "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", part,
    ], check=True, capture_output=True)
    os.replace(part, out_mp4)  # atomic
    return out_mp4
