"""Find and cut the chorus — the highest-energy window — for the teaser.

ffmpeg decodes the audio to mono PCM, numpy builds an RMS loudness profile, and
a sliding window picks the loudest stretch. When several windows tie (>= 94% of
the peak) the latest one wins — the final chorus is usually the fullest.
"""
from __future__ import annotations

import subprocess

import numpy as np

SR = 22050


def _rms_profile(audio: str, ff: str, hop: float = 0.5) -> np.ndarray:
    # cap the decode at 20 min so an unusually long input can't OOM the host
    raw = subprocess.run(
        [ff, "-i", audio, "-t", "1200", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    n = int(SR * hop)
    if len(pcm) < n:
        return np.array([0.0], dtype=np.float32)
    frames = pcm[: len(pcm) // n * n].reshape(-1, n)
    return np.sqrt((frames ** 2).mean(axis=1))


def find_chorus(audio: str, ff: str, length: float = 20.0, hop: float = 0.5,
                tail_guard: float = 3.0) -> float:
    """Return the start time (seconds) of the loudest ``length``-second window,
    excluding the final ``tail_guard`` seconds."""
    rms = _rms_profile(audio, ff, hop)
    win = int(length / hop)
    if len(rms) <= win:
        return 0.0
    energy = np.convolve(rms, np.ones(win), mode="valid")
    limit = len(energy) - int(tail_guard / hop)
    energy = energy[: max(limit, 1)]
    candidates = np.where(energy >= energy.max() * 0.94)[0]
    start = candidates[0]
    for prev, cur in zip(candidates, candidates[1:]):
        if (cur - prev) * hop > 2.0:  # jump to the start of the latest run
            start = cur
    return float(start * hop)


def cut(audio: str, out_path: str, ff: str, start: float | None = None,
        length: float = 20.0) -> tuple[str, float]:
    """Cut ``length`` seconds from ``start`` (auto-detected if None) with a short
    fade in/out → mp3. Returns (path, start)."""
    if start is None:
        start = find_chorus(audio, ff, length)
    subprocess.run([
        ff, "-y", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", audio,
        "-af", f"afade=t=in:d=0.4,afade=t=out:st={length - 0.4:.2f}:d=0.4",
        "-c:a", "libmp3lame", "-b:a", "192k", out_path,
    ], check=True, capture_output=True)
    return out_path, start
