<!-- Pipeline validation: 2026-04-04 -->
> **For AI agents:** This is the CueAPI CLI. Install with `pip install cueapi`. Authenticate with `cueapi login`. Create a cue: `cueapi create --name "task-name" --cron "0 9 * * *" --url https://your-handler.com`. List cues: `cueapi list`. View a cue and its recent executions: `cueapi get <cue-id>`. Your API key can also be set via `CUEAPI_API_KEY` env var. Do not retry on authentication errors.

# CueAPI CLI

Your agents are failing silently. CueAPI tells you when and why.

*Cron has no concept of success. Cue does.*

[![License](https://img.shields.io/badge/license-MIT-black)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/cueapi/)
[![PyPI](https://img.shields.io/pypi/v/cueapi?label=pypi)](https://pypi.org/project/cueapi/)
[![Docs](https://img.shields.io/badge/docs-docs.cueapi.ai-black)](https://docs.cueapi.ai)

The official CLI for [CueAPI](https://cueapi.ai). Manage your cues, check executions, and verify outcomes from the terminal.

Built for AI builders running agents in production. Schedule your agent tasks, confirm delivery, and verify outcomes without leaving the terminal.

---

## Install
```bash
pip install cueapi
```

---

## Quick start
```bash
# Authenticate
cueapi login

# Create your first cue
cueapi create --name "morning-agent-brief" --cron "0 9 * * *" --url https://your-agent.com/run

# See what is scheduled
cueapi list

# Inspect a cue and its recent executions
cueapi get <cue-id>
```

---

## Why CueAPI over cron?

Cron fires a job. That is it. No retries. No delivery confirmation. No outcome tracking. No visibility.

| Feature | Cron | CueAPI |
|---------|------|--------|
| Fires on schedule | Yes | Yes |
| Confirms delivery | No | Yes |
| Tracks outcomes | No | Yes |
| Retries on failure | No | Yes (1, 5, 15 min) |
| Alerts on failure | No | Yes |
| Execution history | No | Yes |

---

## Commands

| Command | Description |
|---|---|
| `cueapi login` | Authenticate and store API key |
| `cueapi whoami` | Show current user and plan |
| `cueapi logout` | Remove local credentials |
| `cueapi quickstart` | Guided first-cue setup |
| `cueapi create` | Create a new cue (supports `--worker`, `--payload`, `--on-failure`) |
| `cueapi list` | List all cues |
| `cueapi get <id>` | Get cue details and recent executions |
| `cueapi update <id>` | Update an existing cue |
| `cueapi pause <id>` | Pause a cue |
| `cueapi resume <id>` | Resume a cue |
| `cueapi delete <id>` | Delete a cue |
| `cueapi fire <id>` | Fire an existing cue immediately, optional `--payload-override` |
| `cueapi executions list` | List historical executions across all cues |
| `cueapi executions list-claimable` | List unclaimed worker executions, filter by `--task` / `--agent` |
| `cueapi executions get <id>` | Fetch one execution by ID |
| `cueapi executions claim <id> --worker-id ID` | Atomically claim an execution |
| `cueapi executions claim-next --worker-id ID [--task]` | Claim the next available execution |
| `cueapi executions heartbeat <id> --worker-id ID` | Extend the claim lease |
| `cueapi executions report-outcome <id> --success/--failure` | Report a write-once outcome |
| `cueapi usage` | Show current usage and limits |
| `cueapi key regenerate` | Regenerate API key |
| `cueapi upgrade` | Open billing |
| `cueapi manage` | Open Stripe billing portal |

---

## Auth

Credentials stored in `~/.config/cueapi/credentials.json`.

Override with env var: `export CUEAPI_API_KEY=cue_sk_your_key`

Or pass inline: `cueapi list --api-key cue_sk_your_key`

---

## Transport modes

The CLI works with both webhook and worker cues. For worker cues running without a public URL, install the worker daemon separately:
```bash
pip install cueapi-worker
```

See [cueapi-python](https://github.com/cueapi/cueapi-python) for the full SDK and worker setup.

---

## Links

- [cueapi.ai](https://cueapi.ai) - hosted service, free tier available
- [cueapi-core](https://github.com/cueapi/cueapi-core) - open source server
- [cueapi-python](https://github.com/cueapi/cueapi-python) - Python SDK
- [Dashboard](https://dashboard.cueapi.ai) - manage cues and view executions
- [Changelog](CHANGELOG.md) - full version history

---

## Releases

Releases are published to PyPI with PEP 740 attestations via GitHub Actions Trusted Publishing.

---

## License

MIT. See [LICENSE](LICENSE).

---

*Built by [Vector Apps](https://vectorapps.ai)*
