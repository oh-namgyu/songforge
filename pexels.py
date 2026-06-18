"""Optional Pexels background-video fetch.

Disabled by default. Pexels content is under the **Pexels License** (NOT CC0):
free to use, but no reselling unaltered copies and identifiable-people/property
limits apply. Set PEXELS_API_KEY to enable; otherwise SongForge uses a generated
gradient background (background.fallback_bg).
"""
from __future__ import annotations

import json
import os
import shutil
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (compatible; SongForge)"


def _download(url: str, dest: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out)  # stream — avoid loading whole mp4 in memory
    return dest


def fetch_videos(query: str, dest_dir: str, api_key: str, n: int = 8,
                 min_w: int = 1280, max_w: int = 1920) -> list[str]:
    """Download up to ``n`` landscape HD clips for ``query``. Returns paths."""
    url = (f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}"
           "&per_page=20&orientation=landscape")
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    jobs = []
    for video in data.get("videos", []):
        if len(jobs) >= n:
            break
        if video.get("duration", 0) < 8:
            continue
        files = [f for f in video["video_files"]
                 if f.get("width") and min_w <= f["width"] <= max_w
                 and f.get("link", "").endswith(".mp4")]
        files.sort(key=lambda f: abs(f["width"] - min_w))
        if files:
            jobs.append(files[0]["link"])
    if not jobs:
        raise RuntimeError(f"no Pexels videos for {query!r}")

    os.makedirs(dest_dir, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(
            lambda iu: _download(iu[1], os.path.join(dest_dir, f"clip{iu[0]}.mp4")),
            enumerate(jobs)))
