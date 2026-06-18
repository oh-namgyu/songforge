"""Build one finished single from a song spec.

spec (lyrics.write_spec) + persona → full song (ACE-Step) → chorus teaser short
(9:16) → lyric music video (16:9) → UPLOAD.md, all in a self-contained folder.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil

import pexels
from ace_client import DEFAULT_VOCAL_STYLE, AceStepClient
from background import fallback_bg, reel
from chorus import cut as chorus_cut
from render import lyric_video, teaser_video
from textcard import render_impact

TEASER_LEN = 20.0
FULL_DUR = 180
MAX_DURATION = 600  # cap a spec-supplied duration to avoid absurd/OOM values


def single_paths(out_dir, slug: str, date: str):
    outdir = os.path.join(str(out_dir), f"{date}_{slug}")
    return outdir, os.path.join(outdir, f"{slug}_full.wav")


def make_full(cfg, spec: dict, persona: dict, date: str | None = None,
              after_audio=None) -> str:
    """spec → full song + teaser short + MV + UPLOAD.md. Returns the folder.

    ``after_audio`` runs right after the audio is retrieved (e.g. stop a locally
    spawned ACE-Step before the long render).
    """
    date = date or datetime.date.today().isoformat()
    slug = spec["slug"]
    outdir, full = single_paths(cfg.out_dir, slug, date)
    os.makedirs(outdir, exist_ok=True)
    vocal = persona.get("vocal") or {}

    if not os.path.exists(full):  # reuse audio on re-render
        AceStepClient(cfg).generate(
            spec["full_lyrics"], full,
            style=vocal.get("style", DEFAULT_VOCAL_STYLE),
            vocal_language=vocal.get("vocal_language", "en"),
            audio_duration=min(max(int(spec.get("duration") or FULL_DUR), 1), MAX_DURATION),
            seed=vocal.get("seed"))
    if after_audio:
        after_audio()

    ff = cfg.ffmpeg
    cut_mp3, chorus_start = chorus_cut(
        full, os.path.join(outdir, f"{slug}_chorus.mp3"), ff, length=TEASER_LEN)
    teaser, mv = _videos(cfg, spec, outdir, full, cut_mp3)

    _write_upload(spec, persona, outdir, date, chorus_start)
    with open(os.path.join(outdir, "spec.json"), "w", encoding="utf-8") as f:
        json.dump(dict(spec, date=date, chorus_start=chorus_start),
                  f, ensure_ascii=False, indent=2)
    return outdir


def _videos(cfg, spec, outdir, full, cut_mp3):
    """Background (Pexels or fallback) + cards → teaser short + lyric MV."""
    ff, slug = cfg.ffmpeg, spec["slug"]
    bg = os.path.join(outdir, "_bg.mp4")
    if not os.path.exists(bg):
        _build_background(cfg, spec, outdir, bg)

    fi, fsub = cfg.font_bold, cfg.font_regular
    lyric = render_impact(spec["hook"], spec["title"], "short",
                          os.path.join(outdir, "_card_lyric.png"), fi, fsub)
    end = render_impact("FULL VERSION\nIN 3 DAYS", f"{spec['title']}  ▶", "short",
                        os.path.join(outdir, "_card_end.png"), fi, fsub)
    teaser = teaser_video(cut_mp3, bg, lyric, end,
                          os.path.join(outdir, f"{slug}_teaser_short.mp4"),
                          ff, "short", switch=TEASER_LEN - 6)

    mv_card = render_impact(spec["title"], spec["hook"].replace("\n", " "), "long",
                            os.path.join(outdir, "_card_mv.png"), fi, fsub)
    mv = lyric_video(full, bg, mv_card,
                     os.path.join(outdir, f"{slug}_full_mv.mp4"), ff, "long")
    return teaser, mv


def _build_background(cfg, spec, outdir, bg):
    """Pexels reel when a key + query exist, else a generated gradient."""
    if cfg.pexels_api_key and spec.get("bg_query"):
        clips_dir = os.path.join(outdir, "_clips")
        try:
            clips = pexels.fetch_videos(spec["bg_query"], clips_dir,
                                        cfg.pexels_api_key, n=8)
            reel(clips, bg, cfg.ffmpeg)
            return
        except Exception:
            pass  # fall through to generated background
        finally:
            shutil.rmtree(clips_dir, ignore_errors=True)
    fallback_bg(bg, cfg.ffmpeg)


UPLOAD_TMPL = """# {title} - release package

> Post the teaser short first, wait ~3 days, then the full music video.
> Publishing is manual by design.

## Schedule
| stage | file | aspect | when |
|---|---|---|---|
| Day 0 | `{slug}_teaser_short.mp4` | 9:16 ({tlen:.0f}s) | {d0} |
| Day +3 | `{slug}_full_mv.mp4` | 16:9 (full song) | {d3} |

## Short (Day 0 - teaser)
**Title**
```
{title} - {name} | full version in 3 days #shorts
```
**Description**
```
{hook}

{description}

Full version out in 3 days.
```
**Tags**
```
{tags}
```

## Music video (Day +3)
**Title**
```
{title} - {name} [Lyric Video]
```
**Description**
```
{title}
{description}

[ Lyrics ]
{lyrics}
```
**Tags**
```
{tags}
```

## Assets
- full song: `{slug}_full.wav`
- chorus cut: `{slug}_chorus.mp3` ({c0:.0f}s - {c1:.0f}s)
- spec: `spec.json`
"""


def _write_upload(spec, persona, outdir, date, chorus_start):
    d0 = datetime.date.fromisoformat(date)
    body = UPLOAD_TMPL.format(
        title=spec["title"], slug=spec["slug"],
        name=persona.get("name", "Unknown Artist"), tlen=TEASER_LEN, d0=d0,
        d3=d0 + datetime.timedelta(days=3),
        hook=spec["hook"].replace("\n", " "),
        description=spec.get("description", ""),
        lyrics=spec["full_lyrics"], tags=", ".join(spec["tags"]),
        c0=chorus_start, c1=chorus_start + TEASER_LEN)
    path = os.path.join(outdir, "UPLOAD.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path
