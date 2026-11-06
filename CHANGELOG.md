# Changelog

All notable changes to this project are listed here. Versions follow [Semantic Versioning](https://semver.org).

## [1.0.0] - 2026-11-06

First release, tested end to end on a Kindle Paperwhite 3 (firmware 5.16.2.1.1) jailbroken with WinterBreak2.

### Added
- Setup script that clones kindle-ai-usage at a pinned commit with LF line endings, applies the agent-filter patch, and writes a `.env` with a fresh ingest token.
- `KINDLETOKEN_AGENTS` collector filter, to count only the chosen agents (for example `claude-code`).
- Kindle Paperwhite 3 framebuffer values (1072x1448, rotation 270) and a 30-minute refresh config.
- Test scriptlets: `fbtest.sh` (FBInk and framebuffer info), `httpstest.sh` (https fetch), `fbshow.sh` (one-shot paint).
- Tailscale Funnel setup that exposes only the dashboard PNG, so the Kindle works on any network.
- Scheduled tasks for the server (at login) and the collector (every 30 minutes).
- `pictures/` scripts to render and serve custom images.
- `.gitattributes` keeping Kindle scripts LF on Windows checkouts.

[1.0.0]: https://github.com/CandyButcher27/kindle-breakin/releases/tag/v1.0.0
