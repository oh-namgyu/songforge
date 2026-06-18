"""ACE-Step HTTP client (bring-your-own music/vocal backend).

Contract is pinned in ACE_STEP_API.md: POST /release_task -> task_id, poll
POST /query_result until done, then resolve the file/wave path from the result.
The audio file must be reachable on the local filesystem (see the limitation
note in ACE_STEP_API.md).
"""
from __future__ import annotations

import json
import os
import shutil
import time
import urllib.parse

import requests

from config import Config

# Sensible defaults; callers (single.py) override per song.
DEFAULT_VOCAL_STYLE = (
    "warm pop song, soft expressive vocals singing the lyrics throughout, "
    "gentle acoustic guitar and light piano, melodic and emotional"
)
INSTRUMENTAL_STYLE = (
    "calm instrumental, no vocals, soft fingerstyle acoustic guitar and gentle "
    "piano, warm strings pad, slow and tender, ambient, sparse, low dynamics"
)


class AceStepError(RuntimeError):
    """ACE-Step returned a failure or never completed."""


class AceStepClient:
    def __init__(self, cfg: Config):
        self.endpoint = cfg.ace_endpoint.rstrip("/")
        self.poll_seconds = cfg.ace_poll_seconds
        self.poll_max = cfg.ace_poll_max

    # ── transport (patched in tests) ────────────────────────────
    def _post(self, path: str, payload: dict) -> dict:
        resp = requests.post(self.endpoint + path, json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> bool:
        """True if the server answers at all (any HTTP status counts)."""
        try:
            requests.get(self.endpoint + "/", timeout=3)
            return True
        except requests.RequestException:
            return False

    # ── generation ──────────────────────────────────────────────
    def generate(self, lyrics: str, out_path: str, *, style: str = DEFAULT_VOCAL_STYLE,
                 vocal_language: str = "en", audio_duration: int = 120,
                 seed: int | None = None, variant: int = 0) -> str:
        """Generate a full song (vocals) from section-tagged lyrics."""
        req = {
            "prompt": style, "lyrics": lyrics, "vocal_language": vocal_language,
            "audio_duration": audio_duration, "inference_steps": 8,
            "guidance_scale": 7.0, "thinking": False, "task_type": "text2music",
        }
        if seed is not None:
            req["seed"] = seed
        return self._run(req, out_path, variant, "song generation")

    def instrumental(self, out_path: str, audio_duration: int, *,
                     style: str = INSTRUMENTAL_STYLE, variant: int = 0) -> str:
        """Generate an instrumental bed (no vocals)."""
        req = {
            "prompt": style, "lyrics": "[instrumental]", "vocal_language": "en",
            "audio_duration": audio_duration, "inference_steps": 8,
            "guidance_scale": 7.0, "thinking": False, "task_type": "text2music",
        }
        return self._run(req, out_path, variant, "instrumental generation")

    # ── core: enqueue -> poll -> retrieve ───────────────────────
    def _run(self, req: dict, out_path: str, variant: int, label: str) -> str:
        task_id = self._post("/release_task", req)["data"]["task_id"]
        for _ in range(self.poll_max):
            time.sleep(self.poll_seconds)
            result = self._post("/query_result", {"task_id_list": [task_id]})
            item = result.get("data")
            item = item[0] if isinstance(item, list) and item else item
            status = item.get("status") if isinstance(item, dict) else None
            if status in (1, "completed", "success"):
                return self._retrieve(item, out_path, variant)
            if status in (2, "failed"):
                raise AceStepError(f"{label} failed: {str(item)[:200]}")
        raise AceStepError(
            f"{label} timed out after {self.poll_max * self.poll_seconds}s")

    @staticmethod
    def _retrieve(item: dict, out_path: str, variant: int) -> str:
        result = item.get("result")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass

        paths: list[str] = []

        def walk(obj):
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if key in ("file", "wave") and isinstance(val, str) and val:
                        paths.append(val)
                    else:
                        walk(val)
            elif isinstance(obj, list):
                for elem in obj:
                    walk(elem)

        walk(result)

        resolved = []
        for path in paths:
            # /v1/audio?path=<url-encoded local path> → take the path param if present
            query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
            resolved.append(query["path"][0] if query.get("path") else path)
        existing = [p for p in dict.fromkeys(resolved) if os.path.exists(p)]
        if not existing:
            raise AceStepError("no audio file found in ACE-Step result")

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        src = existing[min(variant, len(existing) - 1)]
        tmp = out_path + ".part"  # atomic write — no truncated file on interrupt
        shutil.copy(src, tmp)
        os.replace(tmp, out_path)
        return out_path
