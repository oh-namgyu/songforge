# Security Policy

## Reporting a vulnerability
Please report security issues privately via a
[GitHub security advisory](https://github.com/oh-namgyu/songforge/security/advisories/new)
rather than a public issue. We aim to acknowledge reports within a few days.

## Secrets & keys
- All keys (`ANTHROPIC_API_KEY`, `PEXELS_API_KEY`, …) are read from the
  environment or a local **`.env` file, which is gitignored**. Never commit real
  keys; `.env.example` ships with empty placeholders.
- SongForge bundles no credentials. You bring your own LLM and ACE-Step access.
- CI runs a secret scan ([gitleaks](https://github.com/gitleaks/gitleaks)) on
  every push; the repository is also scanned before release.

## Generated artifacts
- Output media, logs, and `*.wav`/`*.mp4` files are gitignored — they are not
  committed and may contain prompt/lyric text you consider private.
- Run output lives in a self-contained folder per song; nothing is sent anywhere
  except to the LLM and ACE-Step endpoints you configure.

## Network surface
- SongForge makes outbound HTTP calls only to: your configured LLM provider,
  your ACE-Step endpoint, and (optionally) the Pexels API. It opens no inbound
  ports and runs no server of its own.
- Endpoint settings (`ACE_STEP_ENDPOINT`, …) are user-controlled. As a local CLI
  this is fine. If you ever wrap SongForge in a service that accepts endpoints
  from untrusted callers, add an allow-list, enforce timeouts, and block
  link-local / cloud-metadata IPs to avoid SSRF.

## Supported versions
The latest released version receives fixes. SongForge targets Python 3.9+.
