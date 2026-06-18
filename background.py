"""Background clip for the video — either a Pexels reel or a generated fallback.

The reel stitches N square-cropped clips so a single background covers both the
9:16 and 16:9 crops. When no Pexels key is set (the default), ``fallback_bg``
renders a calm gradient with ffmpeg — no external assets, no license concerns.
"""
from __future__ import annotations

import os
import subprocess

from render import _cover


def _mean_luma(clip: str, ff: str) -> float:
    """Average brightness of a frame ~3s in (0-255) — to drop near-black clips."""
    from PIL import Image
    tmp = clip + ".luma.png"
    subprocess.run([ff, "-y", "-ss", "3.0", "-i", clip, "-frames:v", "1", tmp],
                   check=True, capture_output=True)
    pixels = list(Image.open(tmp).convert("L").resize((64, 64)).getdata())
    os.remove(tmp)
    return sum(pixels) / len(pixels)


def reel(clips: list[str], out_mp4: str, ff: str, seg: float = 10.0,
         size: int = 1080, min_luma: int = 10) -> str:
    """Concatenate clips (``seg`` s each), square cover-cropped at 25fps."""
    lit = [(c, _mean_luma(c, ff)) for c in clips]
    keep = [c for c, lu in lit if lu >= min_luma]
    if len(keep) < 2:
        keep = [c for c, _ in sorted(lit, key=lambda x: -x[1])[:2]]
    clips = keep or [c for c, _ in lit]

    inputs, filters = [], []
    for i, clip in enumerate(clips):
        inputs += ["-t", f"{seg:.1f}", "-i", clip]
        filters.append(f"[{i}:v]{_cover(size, size)},fps=25[v{i}]")
    fc = (";".join(filters) + ";" + "".join(f"[v{i}]" for i in range(len(clips)))
          + f"concat=n={len(clips)}:v=1:a=0[v]")
    part = out_mp4 + ".part.mp4"
    subprocess.run([ff, "-y", *inputs, "-filter_complex", fc, "-map", "[v]",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    part], check=True, capture_output=True)
    os.replace(part, out_mp4)
    return out_mp4


def fallback_bg(out_mp4: str, ff: str, size: int = 1080, seconds: float = 12.0,
                top: str = "0x16213A", bottom: str = "0x05070D") -> str:
    """A slow vertical gradient — used when no background video is available."""
    src = (f"gradients=s={size}x{size}:c0={top}:c1={bottom}:x0=0:y0=0:"
           f"x1=0:y1={size}:d={seconds}:speed=0.012,fps=25")
    part = out_mp4 + ".part.mp4"
    try:
        subprocess.run([ff, "-y", "-f", "lavfi", "-i", src, "-t", f"{seconds:.1f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        part], check=True, capture_output=True)
    except subprocess.CalledProcessError:  # older ffmpeg without `gradients`
        solid = f"color=c={bottom}:s={size}x{size}:r=25"
        subprocess.run([ff, "-y", "-f", "lavfi", "-i", solid, "-t", f"{seconds:.1f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        part], check=True, capture_output=True)
    os.replace(part, out_mp4)
    return out_mp4
