# Changelog

All notable changes to cueapi-cli will be documented here.

## [Unreleased]

### Added
- **`messages send` + `message-to`: Layer 3 force-file mode (Mike body-verify directive 2026-05-11).** Three body sources accepted (exactly one required): `--message-file <path>` (RECOMMENDED for content with shell metacharacters; zero shell interpolation), `--body-stdin` (read from stdin; for shell-pipe ergonomics), or `--body <inline>` (auto-rejected when content contains `$(...)`, backticks, or `${VAR}`). Inline body with metachars rejected with actionable error suggesting safer paths; override via `--allow-inline-metachars` for legitimate literal-metachar content (e.g., shell-tutorial examples). Closes the caller-side shell-expansion bug class where `BODY="...$(echo X)..."` silently mutates body content at variable-assignment time before reaching the CLI. Design Dock: `cue-message-silent-corruption-substrate-design-2026-05-11`.
- `cueapi message-to <recipient>` top-level wrapper for sending a message by name. Resolves `<recipient>` against your agent roster: `agent_id` (`agt_*`) and slug-form (`slug@user`) pass through unchanged; bare names match case-insensitively against `display_name` and `slug` via `GET /agents`. Same flag set as `messages send` (sans `--to`).
- `agents list --online-only` shortcut for `--status online`. Mutually exclusive with `--status`.
- `agents describe <ref>` alias for `agents get <ref>`.

## [0.2.0] - 2026-05-01

### Added
- `cueapi fire <cue-id>` for ad-hoc one-shot triggers and for using cues as a messaging channel between agents. Optional `--payload-override` (JSON) and `--merge-strategy` (`merge` default, `replace` opt-in). Wraps `POST /v1/cues/{id}/fire`.
- `cueapi executions` subgroup with seven subcommands closing the receive-claim-process-complete loop for worker-transport executions:
  - `executions list` historical executions across all cues.
  - `executions list-claimable [--task] [--agent]` unclaimed executions ready for processing, server-side filtered. Required for single-purpose workers; without a filter, sibling tasks ahead in the LIMIT 50 window starve your handler.
  - `executions get <id>` fetch one execution by ID.
  - `executions claim <id> --worker-id ID` atomically claim a specific execution.
  - `executions claim-next --worker-id ID [--task]` claim the next available execution. With `--task`, the CLI internally fans out (filtered list, pick oldest, claim by ID) since the server's claim endpoint does not accept a task filter today.
  - `executions heartbeat <id> --worker-id ID` extend the claim lease. Sends `worker_id` via the `X-Worker-Id` request header (the server's actual transport for that field).
  - `executions report-outcome <id> --success/--failure [...]` report a write-once outcome with optional `--external-id`, `--result-url`, `--summary`.

### Changed
- `__version__` in `cueapi/__init__.py` had drifted to 0.1.3 while `pyproject.toml` was at 0.1.5. Both now aligned at 0.2.0.

## [0.1.0] - 2025-03-28

### Added
- Initial release of the official CueAPI CLI
- Authentication via magic link (cueapi login)
- Full cue management: create, list, get, pause, resume, delete
- Execution history view (cueapi executions)
- Usage and plan info (cueapi usage, cueapi whoami)
- API key management (cueapi key regenerate)
- Guided quickstart flow (cueapi quickstart)
- Credentials stored in ~/.config/cueapi/credentials.json
- CUEAPI_API_KEY env var support
- --api-key inline flag support
- Python 3.9+ support
