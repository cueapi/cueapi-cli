"""Quickstart command — guided first-cue setup."""
from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import click

from cueapi.client import CueAPIClient
from cueapi.formatting import echo_error, echo_json, echo_success


def do_quickstart(
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
) -> None:
    """Run the quickstart flow: create test cue, verify delivery, clean up."""
    try:
        with CueAPIClient(api_key=api_key, profile=profile) as client:
            click.echo("\nSetting up your first cue...\n")

            # Generate unique echo token
            echo_token = f"qs-{secrets.token_hex(8)}"

            # Step 1: Create one-time cue scheduled for NOW + 15s
            scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=15)
            scheduled_iso = scheduled_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            # The callback URL posts to the echo endpoint
            callback_url = f"{client.api_base}/echo/{echo_token}"

            click.echo("Step 1: Creating a test cue (fires in 15 seconds)...")
            resp = client.post("/cues", json={
                "name": "quickstart-test",
                "description": "Quickstart test cue — safe to delete",
                "schedule": {
                    "type": "once",
                    "at": scheduled_iso,
                    "timezone": "UTC",
                },
                "callback": {
                    "url": callback_url,
                    "method": "POST",
                },
                "payload": {"message": "Your first cue! CueAPI is working."},
            })

            if resp.status_code != 201:
                error = resp.json().get("detail", {}).get("error", {})
                echo_error(error.get("message", f"Failed to create cue (HTTP {resp.status_code})"))
                return

            cue = resp.json()
            cue_id = cue["id"]
            click.echo(f"        Created: {cue_id}")
            click.echo(f"        Scheduled for: {scheduled_iso}\n")

            # Step 2: Wait for delivery
            click.echo("Step 2: Waiting for delivery...")
            deadline = time.time() + 60
            delivered = False
            last_countdown = 15

            while time.time() < deadline:
                remaining = max(0, int(scheduled_time.timestamp() - time.time()))
                if remaining > 0 and remaining < last_countdown:
                    click.echo(f"        {remaining}s...", nl=False)
                    click.echo("\r", nl=False)
                    last_countdown = remaining

                time.sleep(2)

                # Poll echo endpoint
                resp = client.get(f"/echo/{echo_token}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "delivered":
                        click.echo("                              ")  # Clear countdown
                        echo_success("        Callback delivered!\n")
                        click.echo("        Payload:")
                        echo_json(data["payload"])
                        click.echo()
                        delivered = True
                        break

            if not delivered:
                click.echo()
                echo_error("Timed out waiting for delivery.")
                click.echo("\nTroubleshooting:")
                click.echo("  - Is the poller running? (`python -m worker.poller`)")
                click.echo("  - Is the arq worker running? (`python -m worker.main`)")
                click.echo(f"\n  Test cue ID: {cue_id}")
                click.echo(f"  Echo token: {echo_token}")
                return

            # Step 3: Clean up
            click.echo("Step 3: Cleaning up test cue...")
            resp = client.delete(f"/cues/{cue_id}")
            if resp.status_code == 204:
                click.echo("        Deleted.\n")
            else:
                click.echo(f"        (cleanup: HTTP {resp.status_code})\n")

            click.echo("CueAPI is working!\n")
            click.echo("Next steps:")
            click.echo('  cueapi create --name "my-cue" --cron "0 9 * * *" --url https://my-agent.com/webhook')
            click.echo("  Docs: https://docs.cueapi.ai")
            click.echo()

    except click.ClickException as e:
        click.echo(str(e))
