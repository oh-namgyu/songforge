"""Optional: spawn a local ACE-Step server (advanced).

Default usage points ACE_STEP_ENDPOINT at a server you already run. With
ACE_STEP_SPAWN_LOCAL=true (or --spawn-local), SongForge starts ACE-Step itself
using ACE_STEP_DIR / ACE_STEP_UV and stops it when done. Any environment the
server needs (conda, library paths, GPU vars) is the user's responsibility —
set it in your shell before invoking SongForge.
"""
from __future__ import annotations

import signal
import subprocess
import time
import urllib.parse

from ace_client import AceStepClient
from config import Config


def ensure_running(cfg: Config, wait_seconds: int = 600):
    """Return a Popen if we started ACE-Step, or None if it was already up."""
    client = AceStepClient(cfg)
    if client.health():
        return None
    cfg.require_spawn_paths()
    port = str(urllib.parse.urlparse(cfg.ace_endpoint).port or 8001)
    proc = subprocess.Popen(
        [cfg.ace_uv, "run", "--directory", cfg.ace_dir, "acestep-api",
         "--port", port, "--lm-model-path", cfg.ace_lm],
        start_new_session=True)
    deadline = wait_seconds
    while deadline > 0:
        time.sleep(5)
        deadline -= 5
        if proc.poll() is not None:
            raise RuntimeError(f"ACE-Step exited early (code {proc.returncode})")
        if client.health():
            return proc
    stop(proc)
    raise RuntimeError(f"ACE-Step did not become ready within {wait_seconds}s")


def stop(proc) -> None:
    """Stop a server we started (whole process group — uv wraps the real server)."""
    if proc is None or proc.poll() is not None:
        return
    try:
        import os
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=30)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            import os
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
