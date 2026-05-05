"""CueAPI CLI — Click command group and all commands."""
from __future__ import annotations

import json
import webbrowser
from typing import Optional

import click

from cueapi import __version__
from cueapi.auth import do_key_regenerate, do_login, do_logout, do_whoami
from cueapi.client import CueAPIClient
from cueapi.credentials import resolve_api_base
from cueapi.formatting import (
    echo_error,
    echo_info,
    echo_success,
    echo_table,
    format_status,
)
from cueapi.quickstart import do_quickstart


@click.group()
@click.version_option(version=__version__, prog_name="cueapi")
@click.option("--api-key", envvar="CUEAPI_API_KEY", default=None, help="API key (overrides credentials file)")
@click.option("--profile", default=None, help="Credentials profile to use")
@click.pass_context
def main(ctx: click.Context, api_key: Optional[str], profile: Optional[str]) -> None:
    """CueAPI — Your Agents' Cue to Act."""
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["profile"] = profile


# --- Auth commands ---


@main.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Authenticate with CueAPI via browser."""
    profile = ctx.obj.get("profile") or "default"
    api_base = resolve_api_base(profile=profile)
    do_login(api_base=api_base, profile=profile)


@main.command()
@click.pass_context
def whoami(ctx: click.Context) -> None:
    """Show current user info."""
    do_whoami(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile"))


@main.command()
@click.option("--all", "logout_all", is_flag=True, help="Remove all profiles")
@click.pass_context
def logout(ctx: click.Context, logout_all: bool) -> None:
    """Remove stored credentials."""
    profile = ctx.obj.get("profile") or "default"
    do_logout(profile=profile, logout_all=logout_all)


@main.command()
@click.pass_context
def quickstart(ctx: click.Context) -> None:
    """Guided setup: create a test cue, verify delivery, clean up."""
    do_quickstart(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile"))


# --- Cue commands ---


@main.command()
@click.option("--name", required=True, help="Cue name")
@click.option("--cron", default=None, help="Cron expression for recurring cue")
@click.option("--at", "at_time", default=None, help="ISO timestamp for one-time cue")
@click.option("--url", "--callback", default=None, help="Callback URL (not required with --worker)")
@click.option("--method", default="POST", help="HTTP method (default: POST)")
@click.option("--timezone", "tz", default="UTC", help="Timezone (default: UTC)")
@click.option("--payload", default=None, help="JSON payload string")
@click.option("--description", default=None, help="Cue description")
@click.option("--worker", is_flag=True, default=False, help="Use worker transport (no public URL needed)")
@click.option("--on-failure", "on_failure", default=None, help="JSON on_failure config, e.g. '{\"email\": false, \"pause\": true}'")
@click.option(
    "--delivery",
    default=None,
    help='JSON delivery config (timeout_seconds, outcome_deadline_seconds), e.g. \'{"timeout_seconds": 60}\'',
)
@click.option("--alerts", default=None, help="JSON alert config blob")
@click.option(
    "--catch-up",
    "catch_up",
    default=None,
    type=click.Choice(["run_once_if_missed", "skip_missed", "replay_all"]),
    help="Catch-up policy for missed scheduled fires (default: run_once_if_missed).",
)
@click.option(
    "--verification",
    default=None,
    help='JSON verification config (mode, required_assertions), e.g. \'{"mode": "evidence_required"}\'',
)
@click.option(
    "--on-success-fire",
    "on_success_fire",
    default=None,
    help=(
        "Cue ID to fire when an execution of THIS cue reaches a successful terminal state. "
        "Strictly 1:1 chaining; the target cue is validated at create time."
    ),
)
@click.option(
    "--require-payload-override/--no-require-payload-override",
    "require_payload_override",
    default=None,
    help=(
        "Require payload_override on every fire (server-side enforcement, hosted PR #590). "
        "Use on team-comm cues where the payload IS the message; leave unset for cron-style "
        "cues that rely on the stored cue.payload. Fires without payload_override are rejected "
        "with HTTP 400 payload_override_required."
    ),
)
@click.option(
    "--required-keys",
    "required_keys",
    default=None,
    help=(
        "Comma-separated keys that must be present in the resolved override on fire (post-merge). "
        "Missing keys yield HTTP 400 missing_required_payload_keys. Implies --require-payload-override "
        "in spirit but doesn't set it; pass both for full enforcement. Empty string sends an empty list."
    ),
)
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    cron: Optional[str],
    at_time: Optional[str],
    url: str,
    method: str,
    tz: str,
    payload: Optional[str],
    description: Optional[str],
    worker: bool,
    on_failure: Optional[str],
    delivery: Optional[str],
    alerts: Optional[str],
    catch_up: Optional[str],
    verification: Optional[str],
    on_success_fire: Optional[str],
    require_payload_override: Optional[bool],
    required_keys: Optional[str],
) -> None:
    """Create a new cue."""
    if cron and at_time:
        raise click.UsageError("Cannot use both --cron and --at. Choose one.")
    if not cron and not at_time:
        raise click.UsageError("Must specify either --cron or --at.")
    if not worker and not url:
        raise click.UsageError("--url is required unless --worker is set.")

    schedule = {"timezone": tz}
    if cron:
        schedule["type"] = "recurring"
        schedule["cron"] = cron
    else:
        schedule["type"] = "once"
        schedule["at"] = at_time

    body: dict = {
        "name": name,
        "schedule": schedule,
    }

    if worker:
        body["transport"] = "worker"
    else:
        body["callback"] = {"url": url, "method": method}

    if payload:
        try:
            body["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            raise click.UsageError("--payload must be valid JSON")

    if description:
        body["description"] = description

    if on_failure:
        try:
            body["on_failure"] = json.loads(on_failure)
        except json.JSONDecodeError:
            raise click.UsageError("--on-failure must be valid JSON")

    if delivery:
        try:
            body["delivery"] = json.loads(delivery)
        except json.JSONDecodeError:
            raise click.UsageError("--delivery must be valid JSON")

    if alerts:
        try:
            body["alerts"] = json.loads(alerts)
        except json.JSONDecodeError:
            raise click.UsageError("--alerts must be valid JSON")

    if catch_up:
        body["catch_up"] = catch_up

    if verification:
        try:
            body["verification"] = json.loads(verification)
        except json.JSONDecodeError:
            raise click.UsageError("--verification must be valid JSON")

    if on_success_fire:
        body["on_success_fire"] = on_success_fire

    # Hosted PR #590: per-cue opt-in enforcement of payload_override on /fire.
    # `require_payload_override=None` means "not specified" — omit from body so
    # the server's default (false) applies on create.
    if require_payload_override is not None:
        body["require_payload_override"] = require_payload_override

    # `required_keys=None` → omit. Empty string → send `[]` (explicit clear).
    # Non-empty string → split, trim, drop empties.
    if required_keys is not None:
        parsed_keys = [k.strip() for k in required_keys.split(",") if k.strip()]
        body["required_payload_keys"] = parsed_keys

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post("/cues", json=body)
            if resp.status_code == 201:
                cue = resp.json()
                click.echo()
                echo_success(f"Created: {cue['id']}")
                echo_info("Status:", cue["status"])
                if cue.get("next_run"):
                    echo_info("Next run:", cue["next_run"])
                click.echo()
            elif resp.status_code == 403:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cue limit exceeded") + "\nRun `cueapi upgrade` to increase your limit.")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command(name="list")
@click.option("--status", default=None, help="Filter by status (active/paused)")
@click.option("--limit", default=20, type=int, help="Max results")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.pass_context
def list_cues(ctx: click.Context, status: Optional[str], limit: int, offset: int) -> None:
    """List your cues."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status

            resp = client.get("/cues", params=params)
            if resp.status_code != 200:
                echo_error(f"Failed to list cues (HTTP {resp.status_code})")
                return

            data = resp.json()
            cues = data.get("cues", [])
            total = data.get("total", len(cues))

            if not cues:
                click.echo("\nNo cues yet. Create your first one:")
                click.echo('  cueapi create --name "my-cue" --cron "0 9 * * *" --url https://my-agent.com/webhook')
                click.echo('\nOr run `cueapi quickstart` for guided setup.\n')
                return

            click.echo()
            rows = []
            for c in cues:
                next_run = c.get("next_run", "—") or "—"
                if next_run != "—":
                    # Truncate to minute precision
                    next_run = next_run[:16].replace("T", " ") + " UTC"
                rows.append([c["id"], c["name"], format_status(c["status"]), next_run])

            echo_table(
                ["ID", "NAME", "STATUS", "NEXT RUN"],
                rows,
                widths=[22, 20, 12, 22],
            )

            # Summary
            active = sum(1 for c in cues if c["status"] == "active")
            paused = sum(1 for c in cues if c["status"] == "paused")
            parts = []
            if active:
                parts.append(f"{active} active")
            if paused:
                parts.append(f"{paused} paused")
            other = total - active - paused
            if other > 0:
                parts.append(f"{other} other")
            click.echo(f"\n{total} cues ({', '.join(parts)})\n")

    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.argument("cue_id")
@click.pass_context
def get(ctx: click.Context, cue_id: str) -> None:
    """Get detailed info about a cue."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get(f"/cues/{cue_id}")
            if resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return

            c = resp.json()
            click.echo()
            echo_info("Name:", c["name"])
            echo_info("Status:", format_status(c["status"]))

            sched = c.get("schedule", {})
            if sched.get("cron"):
                echo_info("Schedule:", f"{sched['cron']} ({sched.get('timezone', 'UTC')})")
            elif sched.get("at"):
                echo_info("Schedule:", f"One-time: {sched['at']}")

            cb = c.get("callback", {})
            echo_info("Callback:", f"{cb.get('method', 'POST')} {cb.get('url', '')}")

            if c.get("next_run"):
                echo_info("Next run:", c["next_run"])
            if c.get("last_run"):
                echo_info("Last run:", c["last_run"])

            echo_info("Run count:", str(c.get("run_count", 0)))
            echo_info("Created:", c["created_at"])

            if c.get("description"):
                echo_info("Description:", c["description"])

            # Display recent executions
            executions = c.get("executions", [])
            if executions:
                click.echo()
                click.echo("Recent executions:")
                for ex in executions:
                    ts = ex.get("scheduled_for", "")[:16].replace("T", " ")
                    status = ex.get("status", "")
                    if status == "success":
                        mark = click.style("success", fg="green")
                        detail = f"({ex.get('http_status', '')}, {ex.get('attempts', 0)} attempt{'s' if ex.get('attempts', 0) != 1 else ''})"
                    elif status == "failed":
                        mark = click.style("failed", fg="red")
                        err = ex.get("error_message") or f"HTTP {ex.get('http_status', '?')}"
                        detail = f"({err}, {ex.get('attempts', 0)} attempts)"
                    else:
                        mark = click.style(status, fg="yellow")
                        detail = f"({ex.get('attempts', 0)} attempts)"
                    click.echo(f"  {ts}  {mark}  {detail}")

            click.echo()

    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.argument("cue_id")
@click.pass_context
def pause(ctx: click.Context, cue_id: str) -> None:
    """Pause a cue."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.patch(f"/cues/{cue_id}", json={"status": "paused"})
            if resp.status_code == 200:
                c = resp.json()
                echo_success(f"Paused: {cue_id} ({c['name']})")
            elif resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.argument("cue_id")
@click.pass_context
def resume(ctx: click.Context, cue_id: str) -> None:
    """Resume a paused cue."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.patch(f"/cues/{cue_id}", json={"status": "active"})
            if resp.status_code == 200:
                c = resp.json()
                echo_success(f"Resumed: {cue_id} ({c['name']})")
                if c.get("next_run"):
                    echo_info("Next run:", c["next_run"])
            elif resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.argument("cue_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx: click.Context, cue_id: str, yes: bool) -> None:
    """Delete a cue."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            # Get cue name for confirmation
            if not yes:
                resp = client.get(f"/cues/{cue_id}")
                if resp.status_code == 404:
                    echo_error(f"Cue not found: {cue_id}")
                    return
                name = resp.json().get("name", "unknown")
                if not click.confirm(f"Delete {cue_id} ({name})?"):
                    click.echo("Cancelled.")
                    return

            resp = client.delete(f"/cues/{cue_id}")
            if resp.status_code == 204:
                click.echo("Deleted.")
            elif resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
            else:
                echo_error(f"Failed (HTTP {resp.status_code})")
    except click.ClickException as e:
        click.echo(str(e))


# --- Fire (ad-hoc trigger / messaging via cues) ---


@main.command()
@click.argument("cue_id")
@click.option("--payload-override", "payload_override", default=None, help="JSON payload override for this fire only")
@click.option("--merge-strategy", "merge_strategy", type=click.Choice(["merge", "replace"]), default=None, help="How payload-override combines with the cue's stored payload (default: merge, server-side)")
@click.option(
    "--send-at",
    "send_at",
    default=None,
    help=(
        "Optional UTC timestamp (ISO 8601) to schedule this fire for the future. "
        "Server gates dispatch until send-at <= now. Past timestamps are treated as "
        "'fire now' (idempotent — no error). Hosted PR #618."
    ),
)
@click.pass_context
def fire(
    ctx: click.Context,
    cue_id: str,
    payload_override: Optional[str],
    merge_strategy: Optional[str],
    send_at: Optional[str],
) -> None:
    """Fire an existing cue immediately, optionally overriding its payload."""
    body: dict = {}
    if payload_override:
        try:
            body["payload_override"] = json.loads(payload_override)
        except json.JSONDecodeError:
            raise click.UsageError("--payload-override must be valid JSON")
    if merge_strategy:
        body["merge_strategy"] = merge_strategy
    if send_at:
        body["send_at"] = send_at

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/cues/{cue_id}/fire", json=body)
            if resp.status_code in (200, 201, 202):
                data = resp.json()
                exec_id = data.get("id") or data.get("execution_id", "?")
                scheduled = data.get("scheduled_for", "")
                echo_success(f"Fired: {cue_id}")
                echo_info("Execution:", exec_id)
                if scheduled:
                    echo_info("Scheduled:", scheduled)
            elif resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


# --- Billing commands ---


@main.command()
@click.argument("cue_id")
@click.option("--name", default=None, help="New cue name")
@click.option("--cron", default=None, help="New cron expression")
@click.option("--url", "--callback", "url", default=None, help="New callback URL")
@click.option("--payload", default=None, help="New JSON payload")
@click.option("--description", default=None, help="New description")
@click.option("--on-failure", "on_failure", default=None, help="JSON on_failure config")
@click.option(
    "--status",
    default=None,
    type=click.Choice(["active", "paused"]),
    help="New status (alternative to `cueapi pause` / `cueapi resume`).",
)
@click.option("--delivery", default=None, help="JSON delivery config")
@click.option("--alerts", default=None, help="JSON alert config")
@click.option(
    "--catch-up",
    "catch_up",
    default=None,
    type=click.Choice(["run_once_if_missed", "skip_missed", "replay_all"]),
    help="Catch-up policy for missed scheduled fires.",
)
@click.option("--verification", default=None, help="JSON verification config")
@click.option(
    "--on-success-fire",
    "on_success_fire",
    default=None,
    help="Cue ID to fire when this cue's executions succeed (1:1 chaining).",
)
@click.option(
    "--clear-on-success-fire",
    "clear_on_success_fire",
    is_flag=True,
    default=False,
    help="Clear on_success_fire (disable chaining). Mutually exclusive with --on-success-fire.",
)
@click.option(
    "--require-payload-override/--no-require-payload-override",
    "require_payload_override",
    default=None,
    help=(
        "Toggle server-side enforcement of payload_override on fire (hosted PR #590). "
        "--require-payload-override turns it on; --no-require-payload-override turns it off. "
        "Omit to leave unchanged."
    ),
)
@click.option(
    "--required-keys",
    "required_keys",
    default=None,
    help=(
        "Comma-separated keys that must be present in the resolved override on fire. "
        "Empty string sends `[]` (explicit clear). Omit to leave unchanged."
    ),
)
@click.pass_context
def update(ctx: click.Context, cue_id: str, name: Optional[str], cron: Optional[str],
           url: Optional[str], payload: Optional[str], description: Optional[str],
           on_failure: Optional[str],
           status: Optional[str],
           delivery: Optional[str],
           alerts: Optional[str],
           catch_up: Optional[str],
           verification: Optional[str],
           on_success_fire: Optional[str],
           clear_on_success_fire: bool,
           require_payload_override: Optional[bool],
           required_keys: Optional[str]) -> None:
    """Update an existing cue."""
    if on_success_fire and clear_on_success_fire:
        raise click.UsageError("--on-success-fire and --clear-on-success-fire are mutually exclusive.")
    body: dict = {}
    if name:
        body["name"] = name
    if cron:
        body["schedule"] = {"type": "recurring", "cron": cron}
    if url:
        body["callback"] = {"url": url}
    if description:
        body["description"] = description
    if payload:
        try:
            body["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            raise click.UsageError("--payload must be valid JSON")
    if on_failure:
        try:
            body["on_failure"] = json.loads(on_failure)
        except json.JSONDecodeError:
            raise click.UsageError("--on-failure must be valid JSON")
    if status:
        body["status"] = status
    if delivery:
        try:
            body["delivery"] = json.loads(delivery)
        except json.JSONDecodeError:
            raise click.UsageError("--delivery must be valid JSON")
    if alerts:
        try:
            body["alerts"] = json.loads(alerts)
        except json.JSONDecodeError:
            raise click.UsageError("--alerts must be valid JSON")
    if catch_up:
        body["catch_up"] = catch_up
    if verification:
        try:
            body["verification"] = json.loads(verification)
        except json.JSONDecodeError:
            raise click.UsageError("--verification must be valid JSON")
    if on_success_fire:
        body["on_success_fire"] = on_success_fire
    elif clear_on_success_fire:
        # Server uses None to disable chaining; sentinel pattern. Send literal
        # null in JSON.
        body["on_success_fire"] = None

    # Hosted PR #590: tri-state on update — None omits, True/False sends.
    if require_payload_override is not None:
        body["require_payload_override"] = require_payload_override

    # required_keys: None omits; empty string sends []; non-empty splits.
    if required_keys is not None:
        parsed_keys = [k.strip() for k in required_keys.split(",") if k.strip()]
        body["required_payload_keys"] = parsed_keys

    if not body:
        raise click.UsageError("Must specify at least one field to update.")

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.patch(f"/cues/{cue_id}", json=body)
            if resp.status_code == 200:
                c = resp.json()
                echo_success(f"Updated: {cue_id} ({c['name']})")
            elif resp.status_code == 404:
                echo_error(f"Cue not found: {cue_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.pass_context
def upgrade(ctx: click.Context) -> None:
    """Upgrade your plan via Stripe Checkout."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            # Show current plan
            resp = client.get("/usage")
            if resp.status_code == 200:
                data = resp.json()
                plan = data.get("plan", {})
                plan_name = plan if isinstance(plan, str) else plan.get("name", "free")
                click.echo(f"\nCurrent plan: {plan_name.capitalize()}\n")

            click.echo("Available plans:")
            click.echo("  Pro    $9.99/mo   100 cues, 5,000 executions/mo")
            click.echo("  Scale  $49/mo     500 cues, 50,000 executions/mo\n")

            plan_choice = click.prompt("Which plan?", type=click.Choice(["pro", "scale"]))
            interval = click.prompt("Billing interval?", type=click.Choice(["monthly", "annual"]), default="monthly")

            resp = client.post("/billing/checkout", json={"plan": plan_choice, "interval": interval})
            if resp.status_code == 200:
                url = resp.json().get("checkout_url")
                if url:
                    click.echo("\nOpening checkout...")
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass
                    click.echo(f"If browser doesn't open, visit: {url}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.pass_context
def manage(ctx: click.Context) -> None:
    """Open Stripe billing portal."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post("/billing/portal")
            if resp.status_code == 200:
                url = resp.json().get("portal_url")
                if url:
                    click.echo("Opening billing portal...")
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass
                    click.echo(f"If browser doesn't open, visit: {url}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@main.command()
@click.pass_context
def usage(ctx: click.Context) -> None:
    """Show current usage stats."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get("/usage")
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return

            data = resp.json()
            plan = data.get("plan", {})
            cues = data.get("cues", {})
            execs = data.get("executions", {})
            rate = data.get("rate_limit", {})

            click.echo()
            plan_name = plan if isinstance(plan, str) else plan.get("name", "free")
            echo_info("Plan:", plan_name.capitalize())

            active = cues.get("active", 0)
            cue_limit = cues.get("limit", 10)
            echo_info("Active cues:", f"{active} / {cue_limit}")

            used = execs.get("used", 0)
            exec_limit = execs.get("limit", 300)
            pct = (used / exec_limit * 100) if exec_limit > 0 else 0
            echo_info("Executions:", f"{used:,} / {exec_limit:,} ({pct:.1f}%)")

            echo_info("Rate limit:", f"{rate.get('limit', 60)} req/min")
            click.echo()

    except click.ClickException as e:
        click.echo(str(e))


# --- Executions ---


@main.group()
def executions() -> None:
    """Manage executions (worker-transport claim / heartbeat / outcome lifecycle)."""
    pass


@executions.command(name="list")
@click.option("--cue-id", "cue_id", default=None, help="Filter to a specific cue")
@click.option("--status", default=None, help="Filter by execution status")
@click.option(
    "--outcome-state",
    "outcome_state",
    default=None,
    help=(
        "Filter by outcome_state: reported_success / reported_failure / "
        "verified_success / verification_pending / verification_failed / unknown."
    ),
)
@click.option(
    "--result-type",
    "result_type",
    default=None,
    help="Filter by evidence result_type (e.g. 'pr', 'issue', 'comment').",
)
@click.option(
    "--has-evidence",
    "has_evidence",
    is_flag=True,
    default=False,
    help="Filter to executions that reported evidence (evidence_external_id is set).",
)
@click.option(
    "--triggered-by",
    "triggered_by",
    default=None,
    help="Filter by triggered_by: scheduled / manual_fire / chain.",
)
@click.option("--limit", default=20, type=int, help="Max results")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.pass_context
def executions_list(
    ctx: click.Context,
    cue_id: Optional[str],
    status: Optional[str],
    outcome_state: Optional[str],
    result_type: Optional[str],
    has_evidence: bool,
    triggered_by: Optional[str],
    limit: int,
    offset: int,
) -> None:
    """List historical executions across all cues."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {"limit": limit, "offset": offset}
            if cue_id:
                params["cue_id"] = cue_id
            if status:
                params["status"] = status
            if outcome_state:
                params["outcome_state"] = outcome_state
            if result_type:
                params["result_type"] = result_type
            # Server-side `has_evidence` filter is meaningful only when True
            # (it ANDs `evidence_external_id IS NOT NULL`). Unset = no filter,
            # so omit from query params when False rather than send `false`
            # which would still mean the same thing but adds URL noise.
            if has_evidence:
                params["has_evidence"] = "true"
            if triggered_by:
                params["triggered_by"] = triggered_by
            resp = client.get("/executions", params=params)
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            data = resp.json()
            execs = data.get("executions", [])
            if not execs:
                click.echo("\nNo executions found.\n")
                return
            click.echo()
            rows = []
            for ex in execs:
                ts = (ex.get("scheduled_for") or "")[:16].replace("T", " ")
                rows.append([ex.get("id", "?"), ex.get("cue_id", "?"), format_status(ex.get("status", "?")), ts])
            echo_table(["ID", "CUE", "STATUS", "SCHEDULED"], rows, widths=[26, 22, 14, 22])
            click.echo()
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="list-claimable")
@click.option("--task", default=None, help="Filter by payload.task (server-side SQL filter)")
@click.option("--agent", default=None, help="Filter by payload.agent (server-side SQL filter)")
@click.pass_context
def executions_list_claimable(ctx: click.Context, task: Optional[str], agent: Optional[str]) -> None:
    """List unclaimed worker-transport executions ready for processing.

    Filters server-side via task / agent query params. Required for single-purpose
    workers; without --task, sibling tasks ahead in the LIMIT 50 window starve
    your handler.
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {}
            if task:
                params["task"] = task
            if agent:
                params["agent"] = agent
            resp = client.get("/executions/claimable", params=params)
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            data = resp.json()
            execs = data.get("executions", [])
            if not execs:
                filt = []
                if task:
                    filt.append(f"task={task}")
                if agent:
                    filt.append(f"agent={agent}")
                qual = f" ({', '.join(filt)})" if filt else ""
                click.echo(f"\nNo claimable executions{qual}.\n")
                return
            click.echo()
            rows = []
            for ex in execs:
                ts = (ex.get("scheduled_for") or "")[:16].replace("T", " ")
                rows.append([
                    ex.get("execution_id", "?"),
                    ex.get("cue_name", "?"),
                    ex.get("task") or "",
                    ts,
                    str(ex.get("attempt", 1)),
                ])
            echo_table(["ID", "CUE", "TASK", "SCHEDULED", "ATTEMPT"], rows, widths=[26, 22, 22, 18, 8])
            click.echo()
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="get")
@click.argument("execution_id")
@click.pass_context
def executions_get(ctx: click.Context, execution_id: str) -> None:
    """Fetch a single execution by ID."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get(f"/executions/{execution_id}")
            if resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            ex = resp.json()
            click.echo()
            echo_info("ID:", ex.get("id", execution_id))
            echo_info("Cue:", ex.get("cue_id", "?"))
            echo_info("Status:", format_status(ex.get("status", "?")))
            if ex.get("scheduled_for"):
                echo_info("Scheduled:", ex["scheduled_for"])
            if ex.get("started_at"):
                echo_info("Started:", ex["started_at"])
            if ex.get("claimed_by_worker"):
                echo_info("Claimed by:", ex["claimed_by_worker"])
            if ex.get("attempts") is not None:
                echo_info("Attempts:", str(ex["attempts"]))
            if ex.get("http_status") is not None:
                echo_info("HTTP status:", str(ex["http_status"]))
            if ex.get("error_message"):
                echo_info("Error:", ex["error_message"])
            # Effective payload (hosted PR #589): the JSON the handler /
            # webhook actually saw at delivery time. Falls back to the
            # parent cue's stored payload when no per-fire override was
            # set. Surfaced for forensics — what was delivered, not what
            # the cue's stored default looks like at query time.
            if ex.get("payload") is not None:
                echo_info("Payload:", json.dumps(ex["payload"], indent=2, sort_keys=True))
            click.echo()
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="claim")
@click.argument("execution_id")
@click.option("--worker-id", "worker_id", required=True, help="Stable identifier for this worker")
@click.pass_context
def executions_claim(ctx: click.Context, execution_id: str, worker_id: str) -> None:
    """Atomically claim a specific worker-transport execution.

    Returns 409 if already claimed or not eligible.
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/executions/{execution_id}/claim", json={"worker_id": worker_id})
            if resp.status_code == 200:
                data = resp.json()
                echo_success(f"Claimed: {execution_id}")
                if data.get("lease_seconds") is not None:
                    echo_info("Lease:", f"{data['lease_seconds']}s")
            elif resp.status_code == 409:
                echo_error("Not claimable (already claimed, wrong status, or wrong owner)")
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="claim-next")
@click.option("--worker-id", "worker_id", required=True, help="Stable identifier for this worker")
@click.option("--task", default=None, help="Filter to a specific task. Without it, the server picks the oldest pending across any of your worker cues.")
@click.pass_context
def executions_claim_next(ctx: click.Context, worker_id: str, task: Optional[str]) -> None:
    """Claim the next available worker-transport execution.

    With --task, fans out (list-claimable filtered, pick oldest, claim by ID).
    The server's claim endpoint does not accept a task filter today.
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            if task:
                # Fan-out: filtered list + pick oldest + claim by ID. Tiny race
                # window between list and claim is bounded by the atomic claim
                # returning 409, in which case the caller retries.
                lr = client.get("/executions/claimable", params={"task": task})
                if lr.status_code != 200:
                    echo_error(f"Failed to list claimable (HTTP {lr.status_code})")
                    return
                execs = lr.json().get("executions", [])
                if not execs:
                    click.echo(f"\nNo claimable executions for task={task}.\n")
                    return
                next_id = execs[0].get("execution_id")
                resp = client.post(f"/executions/{next_id}/claim", json={"worker_id": worker_id})
                if resp.status_code == 200:
                    data = resp.json()
                    echo_success(f"Claimed: {next_id}")
                    if data.get("lease_seconds") is not None:
                        echo_info("Lease:", f"{data['lease_seconds']}s")
                elif resp.status_code == 409:
                    echo_error(f"Lost the race on {next_id} (another worker beat us). Retry.")
                else:
                    echo_error(f"Failed (HTTP {resp.status_code})")
                return

            resp = client.post("/executions/claim", json={"worker_id": worker_id})
            if resp.status_code == 200:
                data = resp.json()
                echo_success(f"Claimed: {data.get('execution_id', '?')}")
                if data.get("lease_seconds") is not None:
                    echo_info("Lease:", f"{data['lease_seconds']}s")
            elif resp.status_code == 409:
                click.echo("\nNo executions available for claiming.\n")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="heartbeat")
@click.argument("execution_id")
@click.option("--worker-id", "worker_id", required=True, help="Same worker-id used at claim time. Sent as X-Worker-Id header.")
@click.pass_context
def executions_heartbeat(ctx: click.Context, execution_id: str, worker_id: str) -> None:
    """Extend the claim lease on an in-flight execution.

    Returns 403 if worker-id does not match the worker that claimed.
    Returns 409 if the execution is no longer in 'delivering' state.
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            # X-Worker-Id is a request header on the heartbeat endpoint, not body.
            resp = client.post(
                f"/executions/{execution_id}/heartbeat",
                headers={"X-Worker-Id": worker_id},
            )
            if resp.status_code == 200:
                data = resp.json()
                echo_success(f"Heartbeat acknowledged: {execution_id}")
                if data.get("lease_extended_until"):
                    echo_info("Lease until:", data["lease_extended_until"])
            elif resp.status_code == 403:
                echo_error("Worker-id does not match the worker that claimed this execution")
            elif resp.status_code == 409:
                echo_error("Execution is no longer in 'delivering' state")
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="report-outcome")
@click.argument("execution_id")
@click.option("--success/--failure", "success", required=True, help="Outcome: success or failure")
@click.option("--external-id", "external_id", default=None, help="ID from the downstream system")
@click.option("--result-url", "result_url", default=None, help="Public URL proving the work happened")
@click.option("--summary", default=None, help="Short human summary (max 500 chars)")
@click.pass_context
def executions_report_outcome(
    ctx: click.Context,
    execution_id: str,
    success: bool,
    external_id: Optional[str],
    result_url: Optional[str],
    summary: Optional[str],
) -> None:
    """Report the outcome of an execution. Write-once; the outcome is immutable."""
    body: dict = {"success": success}
    if external_id:
        body["external_id"] = external_id
    if result_url:
        body["result_url"] = result_url
    if summary:
        body["summary"] = summary

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/executions/{execution_id}/outcome", json=body)
            if resp.status_code in (200, 201):
                echo_success(f"Outcome recorded: {execution_id}")
                if not success:
                    echo_info("Marked:", "failure")
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            elif resp.status_code == 409:
                echo_error("Outcome already recorded (write-once)")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="replay")
@click.argument("execution_id")
@click.pass_context
def executions_replay(ctx: click.Context, execution_id: str) -> None:
    """Replay a terminal execution.

    Creates a fresh execution against the same cue with the original
    payload_override carried forward. Only valid for terminal states
    (success / failed / missed / outcome_timeout); 409 if the execution
    is still in flight.
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/executions/{execution_id}/replay", json={})
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success(f"Replayed: {execution_id}")
                if data.get("execution_id"):
                    echo_info("New execution:", data["execution_id"])
                if data.get("scheduled_for"):
                    echo_info("Scheduled:", data["scheduled_for"])
                echo_info("Status:", data.get("status", "?"))
                if data.get("triggered_by"):
                    echo_info("Triggered by:", data["triggered_by"])
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cannot replay an execution still in flight"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="verification-pending")
@click.argument("execution_id")
@click.pass_context
def executions_verification_pending(ctx: click.Context, execution_id: str) -> None:
    """Mark an execution's outcome verification as pending."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/executions/{execution_id}/verification-pending", json={})
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success(f"Marked verification-pending: {execution_id}")
                if data.get("outcome_state"):
                    echo_info("Outcome state:", data["outcome_state"])
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cannot transition from current outcome_state"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@executions.command(name="verify")
@click.argument("execution_id")
@click.option(
    "--valid/--invalid",
    "valid",
    default=None,
    help=(
        "Mark verification result. --valid (default behavior, transitions to "
        "verified_success) or --invalid (transitions to verification_failed). "
        "Omitting either flag uses the server default (valid=true)."
    ),
)
@click.option(
    "--reason",
    default=None,
    help=(
        "Optional human-readable reason (max 500 chars). Most useful with "
        "--invalid to record why verification failed."
    ),
)
@click.pass_context
def executions_verify(
    ctx: click.Context,
    execution_id: str,
    valid: Optional[bool],
    reason: Optional[str],
) -> None:
    """Verify or invalidate an execution's evidence."""
    if reason is not None and len(reason) > 500:
        raise click.UsageError("--reason must be ≤500 characters")
    body: dict = {}
    if valid is not None:
        body["valid"] = valid
    if reason:
        body["reason"] = reason
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/executions/{execution_id}/verify", json=body)
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                if valid is False:
                    echo_success(f"Marked verification-failed: {execution_id}")
                else:
                    echo_success(f"Verified: {execution_id}")
                if data.get("outcome_state"):
                    echo_info("Outcome state:", data["outcome_state"])
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Execution not found: {execution_id}")
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cannot transition from current outcome_state"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


main.add_command(executions)


# --- Key management ---


@main.group()
def key() -> None:
    """API key management."""
    pass


@key.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def regenerate(ctx: click.Context, yes: bool) -> None:
    """Regenerate your API key (revokes current key)."""
    do_key_regenerate(
        api_key=ctx.obj.get("api_key"),
        profile=ctx.obj.get("profile"),
        skip_confirm=yes,
    )


@key.group(name="webhook-secret")
def key_webhook_secret() -> None:
    """Manage the user-level webhook signing secret (legacy /v1/auth/webhook-secret).

    For per-agent webhook secrets (Phase 12.1 messaging primitive), use
    `cueapi agents webhook-secret get/regenerate` instead.
    """
    pass


@key_webhook_secret.command(name="get")
@click.pass_context
def key_webhook_secret_get(ctx: click.Context) -> None:
    """Reveal the current user-level webhook signing secret."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get("/auth/webhook-secret")
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_info("Webhook secret:", data.get("webhook_secret", "?"))
                click.echo()
            elif resp.status_code == 404:
                echo_error(
                    "No webhook secret found. The user-level webhook secret is "
                    "auto-provisioned for accounts using the legacy webhook signing "
                    "path; if you only use the messaging primitive (per-agent secrets), "
                    "this is expected. Use `cueapi agents webhook-secret get <ref>` "
                    "for an agent's secret instead."
                )
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@key_webhook_secret.command(name="regenerate")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation")
@click.pass_context
def key_webhook_secret_regenerate(ctx: click.Context, yes: bool) -> None:
    """Rotate the user-level webhook signing secret. Old secret is revoked immediately.

    Server requires the X-Confirm-Destructive: true header (same pattern as
    api-key regenerate). The CLI sends this header automatically when the user
    confirms the prompt (or passes --yes).
    """
    if not yes:
        if not click.confirm(
            "Rotate user-level webhook secret? Current secret will be revoked immediately."
        ):
            click.echo("Aborted.")
            return
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(
                "/auth/webhook-secret/regenerate",
                json={},
                headers={"X-Confirm-Destructive": "true"},
            )
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success("Rotated user-level webhook secret")
                echo_info("New webhook secret (save now — only shown once):", data.get("webhook_secret", "?"))
                click.echo()
            elif resp.status_code == 400:
                # Should be unreachable since the CLI sends the confirmation
                # header automatically; but if the server's contract changes,
                # surface the error rather than swallow it.
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Bad request"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


main.add_command(key)


# --- Messaging primitive: agents command group ---
#
# Mirrors `app/routers/agents.py` in cueapi-hosted. v1 surface covers CRUD
# + webhook-secret management + inbox/sent message lists. The send/get/read/
# ack message lifecycle is in a sibling `cueapi messages` group (separate PR).


@main.group()
def agents() -> None:
    """Manage agents (messaging primitive: identity + webhook secret + inbox)."""
    pass


@agents.command(name="create")
@click.option("--display-name", "display_name", required=True, help="Human-readable name (required, 1-255 chars)")
@click.option("--slug", default=None, help="Per-user unique slug (optional; server derives from display-name when omitted)")
@click.option("--webhook-url", "webhook_url", default=None, help="Push-delivery target. SSRF-validated. Omit for poll-only.")
@click.option("--metadata", default=None, help="JSON metadata blob")
@click.pass_context
def agents_create(
    ctx: click.Context,
    display_name: str,
    slug: Optional[str],
    webhook_url: Optional[str],
    metadata: Optional[str],
) -> None:
    """Create an agent.

    Webhook secret is returned ONLY in this response when --webhook-url is set.
    Subsequent reads omit the secret. Save it now or use webhook-secret regenerate
    to mint a new one (which will revoke the old one).
    """
    body: dict = {"display_name": display_name}
    if slug:
        body["slug"] = slug
    if webhook_url:
        body["webhook_url"] = webhook_url
    if metadata:
        try:
            body["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            raise click.UsageError("--metadata must be valid JSON")
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post("/agents", json=body)
            if resp.status_code == 201:
                a = resp.json()
                click.echo()
                echo_success(f"Created: {a['id']} ({a['slug']})")
                echo_info("Display name:", a["display_name"])
                echo_info("Status:", a.get("status", "?"))
                if a.get("webhook_url"):
                    echo_info("Webhook URL:", a["webhook_url"])
                if a.get("webhook_secret"):
                    # One-time view — only on create + on regenerate. Tell the
                    # user explicitly so they know to copy it now.
                    click.echo()
                    echo_info("Webhook secret (save now — only shown once):", a["webhook_secret"])
                click.echo()
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="list")
@click.option("--status", default=None, type=click.Choice(["online", "offline", "away"]), help="Filter by status")
@click.option(
    "--online-only",
    "online_only",
    is_flag=True,
    default=False,
    help="Shortcut for --status online. Mutually exclusive with --status.",
)
@click.option("--include-deleted", is_flag=True, default=False, help="Include soft-deleted agents")
@click.option("--limit", default=50, type=int, help="Max results (default 50, max 100)")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.pass_context
def agents_list(
    ctx: click.Context,
    status: Optional[str],
    online_only: bool,
    include_deleted: bool,
    limit: int,
    offset: int,
) -> None:
    """List your agents."""
    if online_only and status:
        raise click.UsageError("--online-only and --status are mutually exclusive")
    if online_only:
        status = "online"
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            # Same pattern as `executions list --has-evidence`: only send when
            # True. The server's default is False; sending `false` is no-op
            # and adds URL noise.
            if include_deleted:
                params["include_deleted"] = "true"
            resp = client.get("/agents", params=params)
            if resp.status_code != 200:
                echo_error(f"Failed to list agents (HTTP {resp.status_code})")
                return
            data = resp.json()
            agents_list_data = data.get("agents", [])
            if not agents_list_data:
                click.echo("\nNo agents yet. Create your first one:")
                click.echo('  cueapi agents create --display-name "my-agent"\n')
                return
            click.echo()
            rows = []
            for a in agents_list_data:
                rows.append([
                    a.get("id", "?"),
                    a.get("slug", "?"),
                    a.get("display_name", "?"),
                    format_status(a.get("status", "?")),
                ])
            echo_table(["ID", "SLUG", "DISPLAY NAME", "STATUS"], rows, widths=[24, 24, 28, 12])
            total = data.get("total", len(agents_list_data))
            click.echo(f"\n{total} agents\n")
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="get")
@click.argument("ref")
@click.option("--include-deleted", is_flag=True, default=False, help="Include soft-deleted agents")
@click.pass_context
def agents_get(ctx: click.Context, ref: str, include_deleted: bool) -> None:
    """Get an agent by opaque ID or slug-form (agent@user)."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {}
            if include_deleted:
                params["include_deleted"] = "true"
            resp = client.get(f"/agents/{ref}", params=params)
            if resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            a = resp.json()
            click.echo()
            echo_info("ID:", a.get("id", "?"))
            echo_info("Slug:", a.get("slug", "?"))
            echo_info("Display name:", a.get("display_name", "?"))
            echo_info("Status:", format_status(a.get("status", "?")))
            if a.get("webhook_url"):
                echo_info("Webhook URL:", a["webhook_url"])
            else:
                echo_info("Webhook URL:", "— (poll-only)")
            if a.get("metadata"):
                echo_info("Metadata:", json.dumps(a["metadata"], indent=2, sort_keys=True))
            if a.get("deleted_at"):
                echo_info("Deleted at:", a["deleted_at"])
            click.echo()
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="describe")
@click.argument("ref")
@click.option("--include-deleted", is_flag=True, default=False, help="Include soft-deleted agents")
@click.pass_context
def agents_describe(ctx: click.Context, ref: str, include_deleted: bool) -> None:
    """Alias for `agents get`."""
    ctx.invoke(agents_get, ref=ref, include_deleted=include_deleted)


@agents.command(name="update")
@click.argument("ref")
@click.option("--display-name", "display_name", default=None, help="New display name")
@click.option("--webhook-url", "webhook_url", default=None, help="New webhook URL (push-delivery target)")
@click.option(
    "--clear-webhook-url",
    "clear_webhook_url",
    is_flag=True,
    default=False,
    help="Clear webhook_url (revert to poll-only). Mutually exclusive with --webhook-url.",
)
@click.option("--status", default=None, type=click.Choice(["online", "offline", "away"]), help="New status")
@click.option("--metadata", default=None, help="New JSON metadata blob")
@click.pass_context
def agents_update(
    ctx: click.Context,
    ref: str,
    display_name: Optional[str],
    webhook_url: Optional[str],
    clear_webhook_url: bool,
    status: Optional[str],
    metadata: Optional[str],
) -> None:
    """Update an agent. PATCH semantics — omit fields you don't want to change."""
    if webhook_url and clear_webhook_url:
        raise click.UsageError("--webhook-url and --clear-webhook-url are mutually exclusive.")
    body: dict = {}
    if display_name:
        body["display_name"] = display_name
    if webhook_url:
        body["webhook_url"] = webhook_url
    elif clear_webhook_url:
        # Server uses the explicit-null sentinel pattern (model_fields_set
        # disambiguates "omitted" from "set to null"). Send literal None
        # in JSON to clear.
        body["webhook_url"] = None
    if status:
        body["status"] = status
    if metadata:
        try:
            body["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            raise click.UsageError("--metadata must be valid JSON")
    if not body:
        raise click.UsageError("Must specify at least one field to update.")
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.patch(f"/agents/{ref}", json=body)
            if resp.status_code == 200:
                a = resp.json()
                echo_success(f"Updated: {a.get('id', ref)} ({a.get('slug', '?')})")
            elif resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="delete")
@click.argument("ref")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation")
@click.pass_context
def agents_delete(ctx: click.Context, ref: str, yes: bool) -> None:
    """Soft-delete an agent. Pass --yes to skip the confirmation prompt."""
    if not yes:
        if not click.confirm(f"Delete agent {ref}?"):
            click.echo("Aborted.")
            return
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.delete(f"/agents/{ref}")
            if resp.status_code == 204:
                echo_success(f"Deleted: {ref}")
            elif resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
            else:
                # Best-effort error parsing — DELETE responses typically don't
                # carry a body but a JSON 4xx might.
                try:
                    error = resp.json().get("detail", {}).get("error", {})
                    echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
                except Exception:
                    echo_error(f"Failed (HTTP {resp.status_code})")
    except click.ClickException as e:
        click.echo(str(e))


@agents.group(name="webhook-secret")
def agents_webhook_secret() -> None:
    """Manage an agent's webhook signing secret."""
    pass


@agents_webhook_secret.command(name="get")
@click.argument("ref")
@click.pass_context
def agents_webhook_secret_get(ctx: click.Context, ref: str) -> None:
    """Reveal the agent's webhook signing secret (the agent must own a webhook_url)."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get(f"/agents/{ref}/webhook-secret")
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_info("Webhook secret:", data.get("webhook_secret", "?"))
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Agent not found or has no webhook secret: {ref}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@agents_webhook_secret.command(name="regenerate")
@click.argument("ref")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation")
@click.pass_context
def agents_webhook_secret_regenerate(ctx: click.Context, ref: str, yes: bool) -> None:
    """Rotate the agent's webhook signing secret (revokes the current secret)."""
    if not yes:
        if not click.confirm(f"Rotate webhook secret for {ref}? Current secret will be revoked immediately."):
            click.echo("Aborted.")
            return
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/agents/{ref}/webhook-secret/regenerate", json={})
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success(f"Rotated webhook secret for {ref}")
                echo_info("New webhook secret (save now — only shown once):", data.get("webhook_secret", "?"))
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="inbox")
@click.argument("ref")
@click.option(
    "--state",
    default=None,
    help="Filter by message state (e.g. queued / delivered / read / acked / failed)",
)
@click.option("--limit", default=50, type=int, help="Max results")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.pass_context
def agents_inbox(
    ctx: click.Context,
    ref: str,
    state: Optional[str],
    limit: int,
    offset: int,
) -> None:
    """Poll an agent's inbox (incoming messages)."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {"limit": limit, "offset": offset}
            if state:
                params["state"] = state
            resp = client.get(f"/agents/{ref}/inbox", params=params)
            if resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            data = resp.json()
            messages = data.get("messages", [])
            if not messages:
                click.echo("\nInbox empty.\n")
                return
            click.echo()
            rows = []
            for m in messages:
                from_ref = m.get("from") or {}
                from_label = from_ref.get("slug") or from_ref.get("agent_id", "?")
                subject = (m.get("subject") or "(no subject)")[:30]
                rows.append([
                    m.get("id", "?"),
                    from_label,
                    subject,
                    format_status(m.get("state", "?")),
                ])
            echo_table(["ID", "FROM", "SUBJECT", "STATE"], rows, widths=[20, 22, 32, 12])
            total = data.get("total", len(messages))
            click.echo(f"\n{total} messages\n")
    except click.ClickException as e:
        click.echo(str(e))


@agents.command(name="sent")
@click.argument("ref")
@click.option("--limit", default=50, type=int, help="Max results")
@click.option("--offset", default=0, type=int, help="Offset for pagination")
@click.pass_context
def agents_sent(
    ctx: click.Context,
    ref: str,
    limit: int,
    offset: int,
) -> None:
    """List messages sent by an agent."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            params: dict = {"limit": limit, "offset": offset}
            resp = client.get(f"/agents/{ref}/sent", params=params)
            if resp.status_code == 404:
                echo_error(f"Agent not found: {ref}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            data = resp.json()
            messages = data.get("messages", [])
            if not messages:
                click.echo("\nNo sent messages.\n")
                return
            click.echo()
            rows = []
            for m in messages:
                to_ref = m.get("to") or "?"
                subject = (m.get("subject") or "(no subject)")[:30]
                rows.append([
                    m.get("id", "?"),
                    to_ref,
                    subject,
                    format_status(m.get("state", "?")),
                ])
            echo_table(["ID", "TO", "SUBJECT", "STATE"], rows, widths=[20, 22, 32, 12])
            total = data.get("total", len(messages))
            click.echo(f"\n{total} messages\n")
    except click.ClickException as e:
        click.echo(str(e))


main.add_command(agents)


# --- Workers (fleet visibility for worker-transport users) ---


@main.group()
def workers() -> None:
    """Manage worker fleet (registered workers + heartbeat status)."""
    pass


@workers.command(name="list")
@click.pass_context
def workers_list(ctx: click.Context) -> None:
    """List all registered workers with heartbeat status."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get("/workers")
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            data = resp.json()
            workers_list_data = data.get("workers", [])
            if not workers_list_data:
                click.echo(
                    "\nNo workers registered yet. Workers register automatically by "
                    "sending heartbeats; install cueapi-worker to get started.\n"
                )
                return
            click.echo()
            rows = []
            for w in workers_list_data:
                rows.append([
                    w.get("worker_id", "?"),
                    format_status(w.get("heartbeat_status", "?")),
                    str(w.get("seconds_since_heartbeat", "?")),
                    (w.get("last_heartbeat") or "—")[:19].replace("T", " "),
                ])
            echo_table(
                ["WORKER ID", "STATUS", "SECONDS AGO", "LAST HEARTBEAT"],
                rows,
                widths=[28, 14, 14, 22],
            )
            total = data.get("total", len(workers_list_data))
            click.echo(f"\n{total} workers\n")
    except click.ClickException as e:
        click.echo(str(e))


@workers.command(name="delete")
@click.argument("worker_id")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation")
@click.pass_context
def workers_delete(ctx: click.Context, worker_id: str, yes: bool) -> None:
    """Delete a registered worker.

    Removes the worker row; in-flight executions claimed by this worker
    will be picked up by the stale-recovery loop. Useful for cleaning up
    workers that have been decommissioned.
    """
    if not yes:
        if not click.confirm(f"Delete worker {worker_id}?"):
            click.echo("Aborted.")
            return
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.delete(f"/workers/{worker_id}")
            if resp.status_code == 204:
                echo_success(f"Deleted worker: {worker_id}")
            elif resp.status_code == 404:
                echo_error(f"Worker not found: {worker_id}")
            else:
                try:
                    error = resp.json().get("detail", {}).get("error", {})
                    echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
                except Exception:
                    echo_error(f"Failed (HTTP {resp.status_code})")
    except click.ClickException as e:
        click.echo(str(e))


main.add_command(workers)


# --- Messaging primitive: messages command group ---
#
# Mirrors `app/routers/messages.py` in cueapi-hosted. v1 surface covers the
# message lifecycle (send / get / read / ack). The agent CRUD + inbox lives
# in the sibling `cueapi agents` command group (separate PR).


@main.group()
def messages() -> None:
    """Send and manage messages (messaging primitive: per-message lifecycle)."""
    pass


@messages.command(name="send")
@click.option(
    "--from",
    "from_agent",
    required=True,
    help=(
        "Sender agent — opaque agent_id or slug-form (agent@user). Sent as "
        "the X-Cueapi-From-Agent header. Must be owned by the calling key."
    ),
)
@click.option(
    "--to",
    required=True,
    help="Recipient — opaque agent_id or slug-form (agent@user).",
)
@click.option("--body", "body_text", required=True, help="Message body (1-32768 chars)")
@click.option("--subject", default=None, help="Optional subject line (max 255 chars)")
@click.option(
    "--reply-to",
    "reply_to",
    default=None,
    help="Previous message ID this is replying to (msg_<12 alphanumeric>). thread_id inherits.",
)
@click.option(
    "--priority",
    default=None,
    type=click.IntRange(1, 5),
    help="Priority 1-5 (server default 3). Receiver-pair limits may downgrade priority>3 to 3.",
)
@click.option(
    "--expects-reply",
    "expects_reply",
    is_flag=True,
    default=False,
    help="Mark this message as expecting a reply (boolean flag on send).",
)
@click.option(
    "--reply-to-agent",
    "reply_to_agent",
    default=None,
    help="Decoupled reply target (defaults to the sender). Use when reply should route to a different agent.",
)
@click.option("--metadata", default=None, help="JSON metadata blob")
@click.option(
    "--idempotency-key",
    "idempotency_key",
    default=None,
    help=(
        "Optional Idempotency-Key header (≤255 chars). Same key + same body within "
        "24h returns the existing message with HTTP 200 instead of 201; same key + "
        "different body returns HTTP 409 idempotency_key_conflict."
    ),
)
@click.pass_context
def messages_send(
    ctx: click.Context,
    from_agent: str,
    to: str,
    body_text: str,
    subject: Optional[str],
    reply_to: Optional[str],
    priority: Optional[int],
    expects_reply: bool,
    reply_to_agent: Optional[str],
    metadata: Optional[str],
    idempotency_key: Optional[str],
) -> None:
    """Send a message."""
    body: dict = {"to": to, "body": body_text}
    if subject:
        body["subject"] = subject
    if reply_to:
        body["reply_to"] = reply_to
    if priority is not None:
        body["priority"] = priority
    # Boolean flag — only send when True. Server default is False; sending
    # `false` is no-op + adds payload noise. Pinned in tests.
    if expects_reply:
        body["expects_reply"] = True
    if reply_to_agent:
        body["reply_to_agent"] = reply_to_agent
    if metadata:
        try:
            body["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            raise click.UsageError("--metadata must be valid JSON")

    headers: dict = {"X-Cueapi-From-Agent": from_agent}
    if idempotency_key:
        if len(idempotency_key) > 255:
            raise click.UsageError("--idempotency-key must be ≤255 characters")
        headers["Idempotency-Key"] = idempotency_key

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post("/messages", json=body, headers=headers)
            if resp.status_code in (200, 201):
                m = resp.json()
                click.echo()
                if resp.status_code == 200:
                    # Dedup hit on Idempotency-Key — same key + same body returned
                    # the existing message. Tell the user explicitly so they don't
                    # think a fresh send happened.
                    echo_info("Idempotency-Key dedup hit:", "existing message returned")
                echo_success(f"{'Sent' if resp.status_code == 201 else 'Existing'}: {m.get('id', '?')}")
                if m.get("thread_id"):
                    echo_info("Thread:", m["thread_id"])
                echo_info("Delivery state:", m.get("delivery_state", "?"))
                # Surface server's priority-downgrade signal if present. The
                # server sets X-CueAPI-Priority-Downgraded: true when a
                # receiver-pair priority limit downgrades the message to 3.
                # httpx exposes headers case-insensitive on response.headers.
                downgraded_header = None
                try:
                    downgraded_header = resp.headers.get("X-CueAPI-Priority-Downgraded")
                except Exception:
                    # FakeResp in unit tests doesn't have headers; tolerate.
                    pass
                if downgraded_header == "true":
                    echo_info(
                        "Priority downgraded:",
                        "true (receiver-pair limit applied; message delivered at priority 3)",
                    )
                click.echo()
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                code = error.get("code", "conflict")
                if code == "idempotency_key_conflict":
                    echo_error(
                        "Idempotency-Key conflict — same key was already used with a different body. "
                        "Either reuse the original body or change the key."
                    )
                else:
                    echo_error(error.get("message", f"Conflict (HTTP 409, {code})"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@messages.command(name="get")
@click.argument("msg_id")
@click.pass_context
def messages_get(ctx: click.Context, msg_id: str) -> None:
    """Get a single message by ID."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.get(f"/messages/{msg_id}")
            if resp.status_code == 404:
                echo_error(f"Message not found: {msg_id}")
                return
            if resp.status_code != 200:
                echo_error(f"Failed (HTTP {resp.status_code})")
                return
            m = resp.json()
            click.echo()
            echo_info("ID:", m.get("id", msg_id))
            echo_info("Delivery state:", format_status(m.get("delivery_state", "?")))
            from_ref = m.get("from") or {}
            from_label = from_ref.get("slug") or from_ref.get("agent_id", "?")
            echo_info("From:", from_label)
            echo_info("To:", m.get("to", "?"))
            if m.get("subject"):
                echo_info("Subject:", m["subject"])
            if m.get("thread_id"):
                echo_info("Thread:", m["thread_id"])
            if m.get("reply_to"):
                echo_info("Reply to:", m["reply_to"])
            if m.get("priority") is not None:
                echo_info("Priority:", str(m["priority"]))
            if m.get("expects_reply"):
                echo_info("Expects reply:", "true")
            if m.get("body"):
                # Body is up to 32KB — render verbatim, callers can pipe / grep.
                click.echo()
                click.echo("Body:")
                click.echo(m["body"])
            click.echo()
    except click.ClickException as e:
        click.echo(str(e))


@messages.command(name="read")
@click.argument("msg_id")
@click.pass_context
def messages_read(ctx: click.Context, msg_id: str) -> None:
    """Mark a message as read.

    Idempotent — calling on an already-read message returns 200 unchanged.
    Returns 409 if the message is in a terminal state (acked, expired).
    """
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/messages/{msg_id}/read", json={})
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success(f"Marked read: {msg_id}")
                echo_info("Delivery state:", data.get("delivery_state", "?"))
                if data.get("read_at"):
                    echo_info("Read at:", data["read_at"])
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Message not found: {msg_id}")
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cannot transition from current state (terminal: acked or expired)"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


@messages.command(name="ack")
@click.argument("msg_id")
@click.pass_context
def messages_ack(ctx: click.Context, msg_id: str) -> None:
    """Acknowledge a message — terminal state, no further transitions."""
    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            resp = client.post(f"/messages/{msg_id}/ack", json={})
            if resp.status_code == 200:
                data = resp.json()
                click.echo()
                echo_success(f"Acked: {msg_id}")
                echo_info("Delivery state:", data.get("delivery_state", "?"))
                if data.get("acked_at"):
                    echo_info("Acked at:", data["acked_at"])
                click.echo()
            elif resp.status_code == 404:
                echo_error(f"Message not found: {msg_id}")
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", "Cannot transition from current state"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


main.add_command(messages)


def _resolve_recipient(client, recipient: str) -> str:
    """Resolve a recipient string to an agent_id or slug-form.

    Pass-through when `recipient` already looks like an agent_id (`agt_*`)
    or slug-form (`slug@user`). Otherwise list `/agents` and match
    `display_name` or `slug` case-insensitive exact.
    """
    if recipient.startswith("agt_") or "@" in recipient:
        return recipient

    candidates: list = []
    offset = 0
    while True:
        resp = client.get("/agents", params={"limit": 100, "offset": offset})
        if resp.status_code != 200:
            raise click.ClickException(
                f"Failed to list agents (HTTP {resp.status_code})"
            )
        page = resp.json().get("agents", [])
        candidates.extend(page)
        if len(page) < 100 or offset >= 200:
            break
        offset += 100

    needle = recipient.lower()
    matches = [
        a
        for a in candidates
        if (a.get("display_name") or "").lower() == needle
        or (a.get("slug") or "").lower() == needle
    ]
    if not matches:
        known = sorted({
            a.get("display_name") or a.get("slug") or a.get("id", "?")
            for a in candidates
        })
        hint = ", ".join(known) if known else "(no agents in roster)"
        raise click.ClickException(
            f"No agent matches '{recipient}'. Roster: {hint}"
        )
    if len(matches) > 1:
        ids = ", ".join(m.get("id", "?") for m in matches)
        raise click.ClickException(
            f"'{recipient}' matches {len(matches)} agents: {ids}. "
            "Disambiguate with --to <agent_id> via `messages send`."
        )
    return matches[0].get("id", recipient)


@main.command(name="message-to")
@click.argument("recipient")
@click.option(
    "--from",
    "from_agent",
    required=True,
    help=(
        "Sender agent — opaque agent_id or slug-form (agent@user). Sent as "
        "the X-Cueapi-From-Agent header."
    ),
)
@click.option("--body", "body_text", required=True, help="Message body (1-32768 chars)")
@click.option("--subject", default=None, help="Optional subject line (max 255 chars)")
@click.option(
    "--reply-to",
    "reply_to",
    default=None,
    help="Previous message ID this is replying to (msg_<12 alphanumeric>). thread_id inherits.",
)
@click.option(
    "--priority",
    default=None,
    type=click.IntRange(1, 5),
    help="Priority 1-5 (server default 3). Receiver-pair limits may downgrade priority>3 to 3.",
)
@click.option(
    "--expects-reply",
    "expects_reply",
    is_flag=True,
    default=False,
    help="Mark this message as expecting a reply.",
)
@click.option(
    "--reply-to-agent",
    "reply_to_agent",
    default=None,
    help="Decoupled reply target (defaults to the sender).",
)
@click.option("--metadata", default=None, help="JSON metadata blob")
@click.option(
    "--mode",
    "mode",
    default="auto",
    type=click.Choice(["live", "bg", "inbox", "webhook", "auto"]),
    show_default=True,
    help=(
        "Delivery mode hint. live = recipient's attached Live session, bg = "
        "spawn a fresh background session, inbox = leave in inbox for pull, "
        "webhook = POST to recipient's configured webhook, auto = server "
        "picks the best supported mode based on recipient capabilities. "
        "Server may downgrade if the requested mode isn't supported — see "
        "`Sent via X` in the response."
    ),
)
@click.option(
    "--idempotency-key",
    "idempotency_key",
    default=None,
    help=(
        "Optional Idempotency-Key header (≤255 chars). Same key + same body within "
        "24h returns the existing message with HTTP 200 instead of 201."
    ),
)
@click.pass_context
def message_to(
    ctx: click.Context,
    recipient: str,
    from_agent: str,
    body_text: str,
    subject: Optional[str],
    reply_to: Optional[str],
    priority: Optional[int],
    expects_reply: bool,
    reply_to_agent: Optional[str],
    metadata: Optional[str],
    mode: str,
    idempotency_key: Optional[str],
) -> None:
    """Send a message to a recipient by name, slug, or agent ID.

    Resolves <recipient> against your roster:
      agent_id (agt_*) or slug-form (slug@user) — used as-is.
      bare name — matched case-insensitive against display_name and slug.
    """
    body: dict = {"body": body_text}
    if subject:
        body["subject"] = subject
    if reply_to:
        body["reply_to"] = reply_to
    if priority is not None:
        body["priority"] = priority
    if expects_reply:
        body["expects_reply"] = True
    if reply_to_agent:
        body["reply_to_agent"] = reply_to_agent
    if metadata:
        try:
            body["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            raise click.UsageError("--metadata must be valid JSON")
    # Default-omit discipline: only send delivery_mode when the user opted
    # away from `auto`. Server treats absent == auto, so this avoids payload
    # noise on the common path and keeps wire-format identical to pre-Surface-6
    # senders. `auto` is also redundant to send.
    if mode != "auto":
        body["delivery_mode"] = mode

    headers: dict = {"X-Cueapi-From-Agent": from_agent}
    if idempotency_key:
        if len(idempotency_key) > 255:
            raise click.UsageError("--idempotency-key must be ≤255 characters")
        headers["Idempotency-Key"] = idempotency_key

    try:
        with CueAPIClient(api_key=ctx.obj.get("api_key"), profile=ctx.obj.get("profile")) as client:
            try:
                resolved = _resolve_recipient(client, recipient)
            except click.ClickException as e:
                echo_error(str(e))
                return
            body["to"] = resolved

            resp = client.post("/messages", json=body, headers=headers)
            if resp.status_code in (200, 201):
                m = resp.json()
                click.echo()
                if resp.status_code == 200:
                    echo_info("Idempotency-Key dedup hit:", "existing message returned")
                echo_success(f"{'Sent' if resp.status_code == 201 else 'Existing'}: {m.get('id', '?')}")
                echo_info("To:", resolved)
                if m.get("thread_id"):
                    echo_info("Thread:", m["thread_id"])
                echo_info("Delivery state:", m.get("delivery_state", "?"))
                # Surface the server's chosen delivery mode. The response's
                # `effective_delivery_mode` is the mode the server actually
                # used, which may differ from the requested `mode` if the
                # recipient doesn't support it (e.g. requested live, recipient
                # has no live session, downgraded to inbox).
                effective = m.get("effective_delivery_mode")
                if effective:
                    if mode != "auto" and effective != mode:
                        echo_info(
                            "Sent via:",
                            f"{effective} (requested {mode}, recipient does not support it)",
                        )
                    else:
                        echo_info("Sent via:", effective)
                downgraded_header = None
                try:
                    downgraded_header = resp.headers.get("X-CueAPI-Priority-Downgraded")
                except Exception:
                    pass
                if downgraded_header == "true":
                    echo_info(
                        "Priority downgraded:",
                        "true (receiver-pair limit applied; message delivered at priority 3)",
                    )
                click.echo()
            elif resp.status_code == 409:
                error = resp.json().get("detail", {}).get("error", {})
                code = error.get("code", "conflict")
                if code == "idempotency_key_conflict":
                    echo_error(
                        "Idempotency-Key conflict — same key was already used with a different body. "
                        "Either reuse the original body or change the key."
                    )
                else:
                    echo_error(error.get("message", f"Conflict (HTTP 409, {code})"))
            else:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed (HTTP {resp.status_code})"))
    except click.ClickException as e:
        click.echo(str(e))


if __name__ == "__main__":
    main()
