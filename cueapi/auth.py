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


def _resolve_key_via_session(client, poll_data: dict) -> Optional[str]:
    """Exchange a one-time session_token for a JWT, then call
    GET /v1/auth/key to reveal the user's stored api_key plaintext.

    Used for the existing-user login path where poll_data omits
    ``api_key`` (the server couldn't decrypt it, or the record
    predates encrypted storage). Returns the plaintext api_key on
    success, None on failure — errors are echoed to the user with
    actionable next steps.
    """
    session_token = poll_data.get("session_token")
    if not session_token:
        # No key AND no session token — poll response is malformed or
        # this user hasn't been upgraded to the session-token flow.
        # Shouldn't happen for any production code path as of 2026-04-19
        # (commit adbfe77) but we still want an actionable message.
        click.echo()
        echo_error(
            "Login approved but the server didn't return an api_key or "
            "session_token. Try `cueapi login` again, or contact support."
        )
        return None

    # Exchange session_token (single-use) for a JWT bearer.
    exchange = client.post("/auth/session", json={"token": session_token})
    if exchange.status_code != 200:
        click.echo()
        echo_error(
            f"Could not finalize login (session exchange HTTP "
            f"{exchange.status_code}). Run `cueapi login` to try again."
        )
        return None
    jwt = exchange.json().get("session_token")
    if not jwt:
        click.echo()
        echo_error("Login response missing session_token. Try again.")
        return None

    # Use the JWT as a bearer to reveal the decrypted api_key. /auth/key
    # returns 410 plaintext_unavailable if the encrypted column is empty
    # (no reversible copy exists) — in that case the only remedy is a
    # key rotation, so we surface that guidance directly.
    reveal = client.get(
        "/auth/key",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    if reveal.status_code == 200:
        return reveal.json().get("api_key")
    if reveal.status_code == 410:
        click.echo()
        echo_error(
            "Your API key can't be recovered on this device — the stored "
            "plaintext is no longer available. Run `cueapi key regenerate` "
            "to mint a fresh key, then `cueapi login` again."
        )
        return None
    click.echo()
    echo_error(
        f"Could not retrieve your api_key (HTTP {reveal.status_code}). "
        "Run `cueapi login` to try again or contact support."
    )
    return None


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
                email = poll_data["email"]

                # Resolve the plaintext api_key from the response.
                # Shape varies by user type (server-side logic lives in
                # app/services/device_code_service.py::poll_device_code):
                #   - New user: poll_data contains "api_key" directly.
                #   - Existing user whose api_key_encrypted decrypts:
                #     poll_data ALSO contains "api_key".
                #   - Existing user whose decryption failed or whose
                #     record predates encrypted-storage: poll_data has
                #     NO "api_key", only "session_token" +
                #     "existing_user": true. The CLI must exchange the
                #     session token for a JWT and then call
                #     GET /v1/auth/key to reveal the stored plaintext.
                api_key = poll_data.get("api_key")
                if not api_key:
                    api_key = _resolve_key_via_session(client, poll_data)
                    if not api_key:
                        # _resolve_key_via_session already printed a
                        # user-facing error + next-step guidance.
                        return

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
                # Only show the key plaintext for new users. For existing
                # users it's already on their record from first signup —
                # reprinting it here is a pointless exfil risk (their
                # terminal scrollback, screen-share, etc.).
                if poll_data.get("existing_user"):
                    click.echo(f"Welcome back, {email}.")
                else:
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
