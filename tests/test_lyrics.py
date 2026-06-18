"""Unit tests for the lyric writer — fake provider, no network, no API key."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lyrics import write_spec, validate_spec  # noqa: E402
from providers.fake import FakeProvider, VALID_SPEC  # noqa: E402

PERSONA = {"persona": "a quiet late-night artist", "lyric_rules": ["keep it tender"]}


class WriteSpecTest(unittest.TestCase):
    def test_valid_spec_passes(self):
        spec = write_spec(cfg=None, persona=PERSONA, provider=FakeProvider())
        self.assertEqual(spec["slug"], "city_of_quiet_rain")
        self.assertIn("[chorus]", spec["full_lyrics"])
        self.assertTrue(spec["tags"])

    def test_json_embedded_in_prose_is_extracted(self):
        raw = "Here is your song:\n" + json.dumps(VALID_SPEC) + "\nHope you like it!"
        spec = write_spec(cfg=None, persona=PERSONA, provider=FakeProvider(raw=raw))
        self.assertEqual(spec["title"], "City of Quiet Rain")

    def test_missing_field_raises(self):
        bad = dict(VALID_SPEC)
        del bad["hook"]
        with self.assertRaises(ValueError):
            write_spec(cfg=None, persona=PERSONA, provider=FakeProvider(spec=bad))

    def test_bad_slug_raises(self):
        bad = dict(VALID_SPEC, slug="Has Spaces!")
        with self.assertRaisesRegex(ValueError, "slug"):
            validate_spec(bad)

    def test_no_chorus_raises(self):
        bad = dict(VALID_SPEC, full_lyrics="[verse]\njust a verse")
        with self.assertRaisesRegex(ValueError, "chorus"):
            validate_spec(bad)

    def test_duplicate_slug_raises(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_spec(VALID_SPEC, existing_slugs=["city_of_quiet_rain"])

    def test_no_json_raises(self):
        with self.assertRaisesRegex(ValueError, "No JSON"):
            write_spec(cfg=None, persona=PERSONA, provider=FakeProvider(raw="nope"))

    def test_persona_null_fields_dont_crash(self):
        # A valid JSON persona may carry explicit nulls — must not crash.
        spec = write_spec(cfg=None, persona={"persona": None, "lyric_rules": None},
                          provider=FakeProvider())
        self.assertEqual(spec["slug"], "city_of_quiet_rain")


if __name__ == "__main__":
    unittest.main()
