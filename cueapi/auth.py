"""Auth commands: login, logout, whoami, key regenerate."""
from __future__ import annotations

import secrets
import string
import time
import webbrowser
from typing import Optional

import click

from cueapi.client import CueAPIClient, UnauthClient
from cueapi.credentials import (
    get_profile_info,
    remove_all_credentials,
    remove_credentials,
    resolve_api_base,
    save_credentials,
)
from cueapi.formatting import echo_error, echo_info, echo_success


def _generate_device_code() -> str:
    """Generate a random device code like ABCD-EFGH."""
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(secrets.choice(chars) for _ in range(4))
    part2 = "".join(secrets.choice(chars) for _ in range(4))
    return f"{part1}-{part2}"


def do_login(api_base: Optional[str] = None, profile: str = "default") -> None:
    """Run the device code login flow."""
    base = api_base or resolve_api_base(profile=profile)
    device_code = _generate_device_code()

    with UnauthClient(api_base=base) as client:
        # Step 1: Create device code
        resp = client.post("/auth/device-code", json={"device_code": device_code})
        if resp.status_code != 201:
            error = resp.json().get("detail", {}).get("error", {})
            echo_error(error.get("message", f"Failed to create device code (HTTP {resp.status_code})"))
            return

        data = resp.json()
        verification_url = data["verification_url"]
        expires_in = data["expires_in"]

        # Step 2: Open browser
        click.echo("\nOpening browser to authenticate...")
        try:
            webbrowser.open(verification_url)
        except Exception:
            pass
        click.echo(f"If browser doesn't open, visit: {verification_url}\n")

        # Step 3: Poll
        click.echo("Waiting for authentication...", nl=False)
        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(2)
            click.echo(".", nl=False)

            resp = client.post("/auth/device-code/poll", json={"device_code": device_code})
            if resp.status_code != 200:
                continue

            poll_data = resp.json()
            status = poll_data.get("status")

            if status == "approved":
                api_key = poll_data["api_key"]
                email = poll_data["email"]

                # Save credentials
                save_credentials(
                    profile=profile,
                    data={
                        "api_key": api_key,
                        "email": email,
                        "api_base": base,
                    },
                )

                click.echo()
                echo_success(f"Authenticated as {email}")
                click.echo(f"API key stored in credentials file.\n")
                click.echo(f"Your API key: {api_key}")
                click.echo("(This is the only time your full key will be shown. Save it if you need it elsewhere.)\n")
                click.echo('Run `cueapi quickstart` to create your first cue.')
                return

            if status == "expired":
                click.echo()
                echo_error("Device code expired. Run `cueapi login` to try again.")
                return

        click.echo()
        echo_error("Login timed out. Run `cueapi login` to try again.")


def do_whoami(
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
) -> None:
    """Show current user info."""
    profile_name = profile or "default"
    try:
        with CueAPIClient(api_key=api_key, profile=profile) as client:
            resp = client.get("/auth/me")
            if resp.status_code != 200:
                echo_error(f"Failed to get user info (HTTP {resp.status_code})")
                return

            data = resp.json()

            # Get local key prefix
            prof_info = get_profile_info(profile=profile)
            key_display = "***"
            if prof_info and "api_key" in prof_info:
                key_display = prof_info["api_key"][:7] + "..." + prof_info["api_key"][-4:]

            click.echo()
            echo_info("Email:", data["email"])
            echo_info("Plan:", data["plan"].capitalize())
            echo_info("Active cues:", f"{data['active_cues']} / {data['active_cue_limit']}")
            echo_info("Executions:", f"{data['executions_this_month']} / {data['monthly_execution_limit']} this month")
            echo_info("API key:", key_display)
            echo_info("Profile:", profile_name)
            echo_info("API base:", client.api_base)
            click.echo()
    except click.ClickException:
        click.echo("Not logged in. Run `cueapi login` to authenticate.")


def do_logout(profile: str = "default", logout_all: bool = False) -> None:
    """Remove credentials."""
    if logout_all:
        remove_all_credentials()
        click.echo("Removed all credentials.")
        return

    email = remove_credentials(profile=profile)
    if email:
        click.echo(f"Removed credentials for {email} ({profile} profile).")
    else:
        click.echo(f"No credentials found for profile '{profile}'.")


def do_key_regenerate(
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
    skip_confirm: bool = False,
) -> None:
    """Regenerate API key."""
    if not skip_confirm:
        click.echo()
        click.echo(click.style("Warning: ", fg="yellow") + "This will instantly revoke your current API key.")
        click.echo("  All agents using the old key will stop working.\n")
        if not click.confirm("Proceed?"):
            click.echo("Cancelled.")
            return

    try:
        with CueAPIClient(api_key=api_key, profile=profile) as client:
            resp = client.post("/auth/key/regenerate", headers={"X-Confirm-Destructive": "true"})
            if resp.status_code != 200:
                echo_error(f"Failed to regenerate key (HTTP {resp.status_code})")
                return

            data = resp.json()
            new_key = data["api_key"]

            # Update local credentials
            profile_name = profile or "default"
            prof_info = get_profile_info(profile=profile)
            if prof_info:
                prof_info["api_key"] = new_key
                save_credentials(profile=profile_name, data=prof_info)

            click.echo()
            click.echo(f"New API key: {new_key}")
            click.echo("(This is the only time this key will be shown.)\n")
            click.echo("Local credentials updated.")
    except click.ClickException as e:
        click.echo(str(e))
