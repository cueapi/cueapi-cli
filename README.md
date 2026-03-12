# CueAPI CLI

The official command-line interface for [CueAPI](https://cueapi.ai) — Your Agents' Cue to Act.

CueAPI is a scheduling API for AI agents. Agents register cues (scheduled tasks), CueAPI fires webhooks at the right time. No cron jobs. No infrastructure.

## Install

```bash
pip install cueapi
```

## Quick Start

```bash
cueapi login
cueapi quickstart
cueapi create --name "morning-check" --cron "0 9 * * *" --url https://my-agent.com/webhook
```

## Commands

| Command | Description |
|---|---|
| `cueapi login` | Authenticate and store API key |
| `cueapi whoami` | Show current user and plan |
| `cueapi logout` | Remove local credentials |
| `cueapi quickstart` | Guided first-cue setup |
| `cueapi create` | Create a new cue |
| `cueapi list` | List all cues |
| `cueapi get <id>` | Get cue details |
| `cueapi pause <id>` | Pause a cue |
| `cueapi resume <id>` | Resume a cue |
| `cueapi delete <id>` | Delete a cue |
| `cueapi upgrade` | Open billing |
| `cueapi usage` | Show current usage |
| `cueapi key regenerate` | Regenerate API key |

## Auth

Credentials stored in `~/.config/cueapi/credentials.json`.

Override: `export CUEAPI_API_KEY=cue_sk_your_key` or `--api-key` flag.

## Links

- [Website](https://cueapi.ai)
- [API Reference](https://cueapi.ai/api)
- [Pricing](https://cueapi.ai/pricing)

## License

MIT — Built by [Vector Apps Inc.](https://vectorapps.com)
