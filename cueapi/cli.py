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
@click.option("--url", required=True, help="Callback URL")
@click.option("--method", default="POST", help="HTTP method (default: POST)")
@click.option("--timezone", "tz", default="UTC", help="Timezone (default: UTC)")
@click.option("--payload", default=None, help="JSON payload string")
@click.option("--description", default=None, help="Cue description")
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
) -> None:
    """Create a new cue."""
    if cron and at_time:
        raise click.UsageError("Cannot use both --cron and --at. Choose one.")
    if not cron and not at_time:
        raise click.UsageError("Must specify either --cron or --at.")

    schedule = {"timezone": tz}
    if cron:
        schedule["type"] = "recurring"
        schedule["cron"] = cron
    else:
        schedule["type"] = "once"
        schedule["at"] = at_time

    body = {
        "name": name,
        "schedule": schedule,
        "callback": {"url": url, "method": method},
    }

    if payload:
        try:
            body["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            raise click.UsageError("--payload must be valid JSON")

    if description:
        body["description"] = description

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
                echo_error(error.get("message", "Cue limit exceeded"))
                click.echo("\nRun `cueapi upgrade` to increase your limit.")
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


# --- Billing commands ---


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
                click.echo(f"\nCurrent plan: {plan.get('name', 'Free').capitalize()}\n")

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
            echo_info("Plan:", plan.get("name", "free").capitalize())

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


main.add_command(key)


if __name__ == "__main__":
    main()
