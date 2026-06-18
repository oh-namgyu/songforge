# Third-party components & attribution

SongForge is the orchestration layer. It depends on and integrates the
components below but does **not** redistribute the models, the ffmpeg binary, or
any fonts. Review each component's terms for your own use.

## Runtime Python dependencies
| component | license | role |
|---|---|---|
| [Pillow](https://python-pillow.org/) | HPND (MIT/BSD-style) | caption card rendering |
| [numpy](https://numpy.org/) | BSD-3-Clause | chorus RMS analysis |
| [requests](https://requests.readthedocs.io/) | Apache-2.0 | ACE-Step HTTP client |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | MIT | default lyric LLM provider |

## External backends (bring your own)
| component | license | notes |
|---|---|---|
| [ACE-Step](https://github.com/ace-step/ACE-Step) | Apache-2.0 | music + vocal generation, run as your own HTTP server |
| [ffmpeg](https://ffmpeg.org/) | LGPL-2.1+ / GPL (build-dependent) | invoked as an external binary; install separately |

> The default pipeline invokes the `libx264` and `libmp3lame` encoders — supply an
> ffmpeg build that includes them. Those codecs' licensing and patent terms are
> your responsibility.

## Optional integrations
| component | license | notes |
|---|---|---|
| [Pexels](https://www.pexels.com/license/) videos | **Pexels License — NOT CC0** | free to use, but no reselling unaltered copies and identifiable-people/property limits apply. Disabled unless `PEXELS_API_KEY` is set; default uses a generated gradient background. |
| Caption fonts | user-supplied | not bundled. [OFL](https://openfontlicense.org/) fonts (e.g. Noto) recommended. |

## Provenance / re-licensing
SongForge was extracted and generalized from the author's own prior project and
is released under Apache-2.0. No third-party copyleft source is vendored into
this repository.

## Generated content
Lyrics (via the configured LLM) and audio (via ACE-Step) are subject to those
providers' terms of use. SongForge asserts no ownership over generated output;
clearing rights for publication is the user's responsibility.
