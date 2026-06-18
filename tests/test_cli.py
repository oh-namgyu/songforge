"""CLI argument/validation tests — no ACE-Step, no network."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import songforge  # noqa: E402


class CliTest(unittest.TestCase):
    def test_requires_topic_or_spec(self):
        with self.assertRaises(SystemExit):
            songforge.main([])

    def test_missing_spec_file_exits(self):
        with self.assertRaises(SystemExit):
            songforge.main(["--spec", "/no/such/spec.json"])

    def test_invalid_spec_exits(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"slug": "x"}, f)  # missing required fields + bad slug
            path = f.name
        try:
            with self.assertRaises(SystemExit):
                songforge.main(["--spec", path])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
