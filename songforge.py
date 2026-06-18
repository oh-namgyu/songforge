#!/usr/bin/env python3
"""SongForge — turn a topic into a finished, publishable song package.

    python songforge.py --topic "rainy city at 3am"        # write lyrics + build
    python songforge.py --spec my_song.json                # reuse a spec (no LLM)
    python songforge.py --topic "..." --persona me.json --out ./out
    python songforge.py --topic "..." --resume             # continue a failed run

Output: <out>/<date>_<slug>/ with the full song, a 9:16 teaser short, a 16:9
music video, UPLOAD.md, and status.json.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import sys
from pathlib import Path

import ace_spawn
from config import load
from lyrics import validate_spec, write_spec
from single import make_full, single_paths

DEFAULT_PERSONA = {"name": "Unknown Artist", "persona": "", "lyric_rules": [], "vocal": {}}


def _read_json(path, default=None):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _ledger_path(cfg):
    return os.path.join(str(cfg.out_dir), "ledger.json")


def _append_ledger(cfg, entry):
    ledger = _read_json(_ledger_path(cfg), []) or []
    ledger = [e for e in ledger if e.get("slug") != entry["slug"]] + [entry]
    os.makedirs(str(cfg.out_dir), exist_ok=True)
    with open(_ledger_path(cfg), "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)


def _resolve_spec(cfg, args, persona):
    if args.spec:
        spec = _read_json(args.spec)
        if spec is None:
            sys.exit(f"spec not found: {args.spec}")
        try:
            validate_spec(spec)
        except ValueError as exc:
            sys.exit(f"invalid spec: {exc}")
        return spec
    ledger = _read_json(_ledger_path(cfg), []) or []
    recent = [e.get("theme") for e in ledger if e.get("theme")][-20:]
    existing = [e.get("slug") for e in ledger]
    if args.topic:
        persona = dict(persona,
                       persona=((persona.get("persona") or "") +
                                f"\n\nWrite about: {args.topic}").strip())
    print("writing lyrics...", flush=True)
    try:
        return write_spec(cfg, persona, recent_themes=recent, existing_slugs=existing)
    except ValueError as exc:
        sys.exit(f"lyric generation failed (invalid model output): {exc}")


def _write_status(outdir, **fields):
    with open(os.path.join(outdir, "status.json"), "w", encoding="utf-8") as f:
        json.dump(fields, f, ensure_ascii=False, indent=2)


def _build_parser():
    ap = argparse.ArgumentParser(description="SongForge — topic -> finished single")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help="theme to write a new song about (uses the LLM)")
    src.add_argument("--spec", help="path to an existing song spec JSON (skips the LLM)")
    ap.add_argument("--persona", help="persona JSON (default: persona.example.json)")
    ap.add_argument("--out", help="output directory (overrides SONGFORGE_OUT_DIR)")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    rebuild = ap.add_mutually_exclusive_group()
    rebuild.add_argument("--resume", action="store_true",
                         help="reuse artifacts from a previous (failed) run")
    rebuild.add_argument("--overwrite", action="store_true",
                         help="delete any existing output for this song first")
    ap.add_argument("--spawn-local", action="store_true",
                    help="spawn a local ACE-Step server (needs ACE_STEP_DIR/UV)")
    return ap


def _load_persona(args):
    here = os.path.dirname(os.path.abspath(__file__))
    return (_read_json(args.persona)
            or _read_json(os.path.join(here, "persona.example.json"))
            or DEFAULT_PERSONA)


def _prepare_outdir(cfg, spec, args):
    outdir, _ = single_paths(cfg.out_dir, spec["slug"], args.date)
    if os.path.exists(outdir) and not args.resume:
        status = _read_json(os.path.join(outdir, "status.json"), {})
        if status.get("complete") and not args.overwrite:
            sys.exit(f"already complete: {outdir} (use --overwrite to rebuild)")
        if args.overwrite:
            shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
    _write_status(outdir, slug=spec["slug"], date=args.date, complete=False)
    return outdir


def _build(cfg, spec, persona, args):
    proc = None
    if cfg.ace_spawn_local:
        print("ensuring local ACE-Step...", flush=True)
        proc = ace_spawn.ensure_running(cfg)
    try:
        result = make_full(cfg, spec, persona, date=args.date,
                           after_audio=(lambda: ace_spawn.stop(proc)) if proc else None)
    finally:
        ace_spawn.stop(proc)
    _write_status(result, slug=spec["slug"], date=args.date, complete=True)
    _append_ledger(cfg, {"slug": spec["slug"], "date": args.date,
                         "title": spec.get("title"), "theme": spec.get("theme"),
                         "dir": result})
    return result


def main(argv=None):
    args = _build_parser().parse_args(argv)
    cfg = load()
    if args.out:
        cfg.out_dir = Path(args.out).expanduser()
    if args.spawn_local:
        cfg.ace_spawn_local = True

    persona = _load_persona(args)
    spec = _resolve_spec(cfg, args, persona)
    _prepare_outdir(cfg, spec, args)
    result = _build(cfg, spec, persona, args)
    print(f"\n done: {result}", flush=True)
    print("  see UPLOAD.md for the publishing plan (publish manually).", flush=True)
    return result


if __name__ == "__main__":
    main()
