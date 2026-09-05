# SongForge

[![CI](https://github.com/oh-namgyu/songforge/actions/workflows/ci.yml/badge.svg)](https://github.com/oh-namgyu/songforge/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/oh-namgyu/songforge)](https://github.com/oh-namgyu/songforge/releases)

> **한글 요약** — 주제 하나를 완성곡 패키지로 만듭니다 — AI 작사 → 작곡+보컬(ACE-Step) → 후렴 감지 → 9:16 쇼츠와 16:9 뮤직비디오 렌더 → 업로드 플랜까지 자동화합니다.

Turn a **topic** into a **finished, publishable song package** — AI lyrics →
music + vocals → automatic chorus detection → a 9:16 short *and* a 16:9 music
video → an upload-cadence plan. One command, one self-contained output folder.

Most music-generation tools stop at the `.wav`. SongForge's value is the layer
**after** the model: the chorus-cut teaser, the dual-format publishable videos,
and the release plan.

```
topic / persona
   │  LLMProvider adapter  (default: Anthropic Claude)
   ▼  lyrics spec (JSON)
ACE-Step backend          (Apache-2.0, bring your own)
   ▼  full song .wav (with vocals)
chorus detection (RMS)  →  teaser cut
   ▼
9:16 teaser short  +  16:9 music video  +  UPLOAD.md  +  status.json
   ▼
<out>/<date>_<slug>/
```

## What it is (and isn't)
- **Is:** the orchestration glue + an opinionated video/publishing funnel.
- **Isn't:** a music model (you bring [ACE-Step](https://github.com/ace-step/ACE-Step)),
  a YouTube auto-uploader (it stops at `UPLOAD.md`), or a DAW.

## Requirements
- **Python 3.10+**
- **ffmpeg** on your `PATH` (or set `FFMPEG_PATH`)
- An **[ACE-Step](https://github.com/ace-step/ACE-Step) server** you can reach over
  HTTP — see [ACE_STEP_API.md](ACE_STEP_API.md). (Apache-2.0; GPU/Apple-Silicon recommended.)
- An **LLM API key** for lyrics (default: `ANTHROPIC_API_KEY`)
- *Optional:* a `PEXELS_API_KEY` for background video, and TTF fonts for captions.
  Without them, SongForge uses a generated gradient background and a default font.

## Install
```bash
git clone https://github.com/oh-namgyu/songforge
cd songforge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env
python config.py            # sanity-check your configuration
```

## Configure
All machine-specific settings live in `.env` (gitignored). See
[.env.example](.env.example). The essentials:

| variable | meaning |
|---|---|
| `ANTHROPIC_API_KEY` | lyric-writer key (default provider) |
| `ACE_STEP_ENDPOINT` | your ACE-Step server (default `http://127.0.0.1:8001`) |
| `FFMPEG_PATH` | ffmpeg binary (default `ffmpeg`) |
| `FONT_REGULAR` / `FONT_BOLD` | caption fonts (optional; OFL fonts recommended) |
| `PEXELS_API_KEY` | optional background video (Pexels License — **not** CC0) |

## Usage
```bash
# Write a brand-new song about a topic and build the whole package:
python songforge.py --topic "a sleepless city at 3am"

# Reuse an existing spec (skips the LLM entirely):
python songforge.py --spec my_song.json

# Pick a persona, output dir, resume a failed run:
python songforge.py --topic "..." --persona me.json --out ./out --resume

# Force a clean rebuild, or let SongForge run a local ACE-Step server:
python songforge.py --spec my_song.json --overwrite
python songforge.py --topic "..." --spawn-local
```

Each run produces `<out>/<date>_<slug>/`:
```
<slug>_full.wav            full song (vocals)
<slug>_chorus.mp3          detected chorus, cut for the teaser
<slug>_teaser_short.mp4    9:16 short  (chorus + caption + end card)
<slug>_full_mv.mp4         16:9 music video
UPLOAD.md                  titles, descriptions, tags, posting schedule
spec.json / status.json    the spec used + run manifest
```

## The song spec
Lyrics are produced as a JSON **spec** (contract in
[schemas/song_spec.schema.json](schemas/song_spec.schema.json)): `slug`, `title`,
`theme`, `full_lyrics` (section-tagged, with a `[chorus]`), `hook`, optional
`bg_query` / `description`, and `tags`. Provide your own with `--spec`.

## Swapping the LLM
Lyric generation goes through a small `LLMProvider` interface
([providers/](providers/)). Anthropic is the default; an OpenAI stub shows the
shape. To add a backend, implement `generate()` and register it in
`providers/__init__.py`, then set `LLM_PROVIDER`.

## Bring-your-own ACE-Step
SongForge talks to ACE-Step over HTTP and never bundles the model. Point
`ACE_STEP_ENDPOINT` at a server you run, or set `ACE_STEP_SPAWN_LOCAL=true` (with
`ACE_STEP_DIR` / `ACE_STEP_UV`) to have SongForge start and stop it for you. The
client/server must share a filesystem — see [ACE_STEP_API.md](ACE_STEP_API.md).

## Testing
```bash
python -m unittest discover -s tests
```
Tests use a fake LLM provider, a mock ACE-Step transport, and a synthetic audio
fixture — no API key, no model, no network required.

## License

Apache-2.0 — see [LICENSE](LICENSE). Security policy: [SECURITY.md](SECURITY.md).
Third-party components and their terms are listed in
[THIRD_PARTY.md](THIRD_PARTY.md) and [NOTICE](NOTICE). Generated lyrics and audio
follow the terms of the backends you choose; SongForge claims no ownership over
your output.
