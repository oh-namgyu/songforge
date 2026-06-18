"""Chorus detection test on a synthetic fixture (loud section in the middle)."""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load  # noqa: E402
from chorus import find_chorus  # noqa: E402

FF = load().ffmpeg


def _have_ffmpeg():
    try:
        subprocess.run([FF, "-version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _make_fixture(path):
    """12s quiet + 8s loud + 12s quiet → loud chorus at 12-20s."""
    subprocess.run([
        FF, "-y",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=12",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=12",
        "-filter_complex",
        "[0]volume=0.05[a];[1]volume=0.9[b];[2]volume=0.05[c];"
        "[a][b][c]concat=n=3:v=0:a=1[out]",
        "-map", "[out]", path,
    ], check=True, capture_output=True)


@unittest.skipUnless(_have_ffmpeg(), "ffmpeg not available")
class ChorusTest(unittest.TestCase):
    def test_finds_loud_section(self):
        with tempfile.TemporaryDirectory() as d:
            fixture = os.path.join(d, "fixture.wav")
            _make_fixture(fixture)
            start = find_chorus(fixture, FF, length=6.0, tail_guard=3.0)
            # loud region is 12-20s; the loudest 6s window should start in there
            self.assertGreaterEqual(start, 10.0)
            self.assertLessEqual(start, 18.0)


if __name__ == "__main__":
    unittest.main()
