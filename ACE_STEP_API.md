# ACE-Step backend contract

SongForge treats [ACE-Step](https://github.com/ace-step/ACE-Step) (Apache-2.0)
as a **bring-your-own** music/vocal generation backend, reached over HTTP at
`ACE_STEP_ENDPOINT` (default `http://127.0.0.1:8001`). This file pins the exact
request/response contract the client depends on, so the integration is fixed in
the plan rather than discovered at runtime. It is extracted from a known-working
implementation; the client is verified against a mock implementing this contract
plus one real smoke run.

## Endpoints

### `POST /release_task` — enqueue a generation job
Request body (JSON):

| field | type | notes |
|---|---|---|
| `prompt` | string | style/genre description (e.g. "soft female vocals, warm acoustic") |
| `lyrics` | string | section-tagged lyrics, e.g. `[verse]\n...\n[chorus]\n...`; `[instrumental]` for no vocals |
| `vocal_language` | string | `"en"` / `"ko"` … vocal language hint |
| `audio_duration` | number | seconds |
| `inference_steps` | int | e.g. `8` |
| `guidance_scale` | number | e.g. `7.0` |
| `thinking` | bool | `false` |
| `task_type` | string | `"text2music"` |
| `seed` | int | optional; fixes reproducibility (stable chorus cut / persona consistency) |

Response: `{"data": {"task_id": "<id>"}}`

### `POST /query_result` — poll a job
Request body: `{"task_id_list": ["<id>"]}`

Response: `{"data": [ {"status": <s>, "result": <r>} ]}` (the item may also come
back as a bare object rather than a 1-element list — handle both).

- `status` ∈ `1 | "completed" | "success"` → **done**
- `status` ∈ `2 | "failed"` → **error** (surface `result` text)
- otherwise → still running

`result` is JSON (sometimes a JSON-encoded string — parse if `str`). Walk it for
`"file"` / `"wave"` string values; each is either a filesystem path or a URL of
the form `/v1/audio?path=<url-encoded local path>` (take the `path` query param).

## Polling

Poll every `ACE_STEP_POLL_SECONDS` (default `8`) up to `ACE_STEP_POLL_MAX`
(default `120`) times → ceiling ≈ 16 minutes. Tune for slower hardware.

## Output retrieval & limitation

The resolved audio path must exist on the **same filesystem as the client** —
ACE-Step writes the file locally and returns its path. So the client and the
ACE-Step server must share a filesystem (same host, or a shared mount). Running
ACE-Step on a remote host without a shared mount is **not** supported by this
contract. The client copies the file atomically (`*.part` → final).

## Local spawn (optional)

With `ACE_STEP_SPAWN_LOCAL=true` (+ `ACE_STEP_DIR`, `ACE_STEP_UV`) SongForge can
start the server itself and stop it after the audio is retrieved (useful on
memory-constrained machines). Default is `false` — point at a server you manage.
