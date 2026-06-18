"""Mock contract tests for the ACE-Step client — no server, no model.

Patches the HTTP transport (`_post`) to replay the documented contract and
verifies polling, terminal states, and file retrieval (including the
`/v1/audio?path=` URL form).
"""
import os
import sys
import tempfile
import unittest
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ace_client  # noqa: E402
from ace_client import AceStepClient, AceStepError  # noqa: E402


class _Cfg:
    ace_endpoint = "http://127.0.0.1:8001"
    ace_poll_seconds = 0  # don't actually sleep in tests
    ace_poll_max = 5


def _client_with(responses):
    """Build a client whose `_post` returns queued responses in order, and
    whose `time.sleep` is a no-op."""
    client = AceStepClient(_Cfg())
    calls = iter(responses)
    client._post = lambda path, payload: next(calls)
    return client


class AceClientTest(unittest.TestCase):
    def setUp(self):
        self._real_sleep = ace_client.time.sleep
        ace_client.time.sleep = lambda *_: None

    def tearDown(self):
        ace_client.time.sleep = self._real_sleep

    def test_poll_until_complete_and_retrieve(self):
        with tempfile.TemporaryDirectory() as d:
            audio = os.path.join(d, "song.wav")
            with open(audio, "wb") as f:
                f.write(b"RIFFfake")
            out = os.path.join(d, "out.wav")
            client = _client_with([
                {"data": {"task_id": "t1"}},                 # release_task
                {"data": [{"status": 0}]},                   # still running
                {"data": [{"status": 1, "result": {"file": audio}}]},  # done
            ])
            result = client.instrumental(out, audio_duration=10)
            self.assertEqual(result, out)
            self.assertTrue(os.path.exists(out))

    def test_audio_url_path_form_is_resolved(self):
        with tempfile.TemporaryDirectory() as d:
            audio = os.path.join(d, "v.wav")
            open(audio, "wb").close()
            out = os.path.join(d, "out.wav")
            url = "/v1/audio?path=" + urllib.parse.quote(audio)
            client = _client_with([
                {"data": {"task_id": "t1"}},
                {"data": [{"status": "success", "result": {"wave": url}}]},
            ])
            self.assertEqual(client.instrumental(out, audio_duration=10), out)

    def test_failed_status_raises(self):
        client = _client_with([
            {"data": {"task_id": "t1"}},
            {"data": [{"status": 2, "result": "boom"}]},
        ])
        with self.assertRaisesRegex(AceStepError, "failed"):
            client.instrumental("/tmp/nope.wav", audio_duration=10)

    def test_timeout_raises(self):
        running = {"data": [{"status": 0}]}
        client = _client_with([{"data": {"task_id": "t1"}}] + [running] * 5)
        with self.assertRaisesRegex(AceStepError, "timed out"):
            client.instrumental("/tmp/nope.wav", audio_duration=10)

    def test_missing_file_raises(self):
        client = _client_with([
            {"data": {"task_id": "t1"}},
            {"data": [{"status": 1, "result": {"file": "/no/such/file.wav"}}]},
        ])
        with self.assertRaisesRegex(AceStepError, "no audio file"):
            client.instrumental("/tmp/nope.wav", audio_duration=10)


if __name__ == "__main__":
    unittest.main()
