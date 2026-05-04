"""Tests for the existing-user login path in cueapi.auth.do_login.

Backend commit adbfe77 changed POST /v1/auth/device-code/poll so the
response can approve a login WITHOUT returning an api_key (for
existing users whose encrypted record couldn't be decrypted). Before
this fix, do_login did `poll_data["api_key"]` and crashed with
KeyError on every existing-user login. These tests pin the new flow
so the regression can't return silently.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cueapi import auth


@pytest.fixture
def poll_responses(monkeypatch):
    """Feed a scripted series of UnauthClient.get / .post responses.

    Returns (script, used). `script` is a list the caller mutates
    to specify response shape; `used` captures what the test code
    actually called, for assertion.
    """
    script = {"post": [], "get": []}
    used = {"post": [], "get": []}

    def _make_response(status_code: int, body: dict | None = None):
        r = MagicMock()
        r.status_code = status_code
        r.json.return_value = body or {}
        return r

    class FakeUnauth:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def post(self, path, **kwargs):
            used["post"].append({"path": path, **kwargs})
            sc, body = script["post"].pop(0)
            return _make_response(sc, body)
        def get(self, path, **kwargs):
            used["get"].append({"path": path, **kwargs})
            sc, body = script["get"].pop(0)
            return _make_response(sc, body)

    monkeypatch.setattr(auth, "UnauthClient", FakeUnauth)
    # Skip the browser open and sleep so tests run instantly.
    monkeypatch.setattr(auth, "webbrowser", MagicMock())
    monkeypatch.setattr(auth.time, "sleep", lambda _s: None)

    return script, used


@pytest.fixture
def captured_saves(monkeypatch):
    """Capture save_credentials calls so we can assert what got stored."""
    calls = []

    def _capture(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(auth, "save_credentials", _capture)
    monkeypatch.setattr(auth, "resolve_api_base", lambda profile=None: "https://api.cueapi.ai/v1")
    return calls


class TestNewUserLogin:
    """New-user poll responses include api_key directly — unchanged
    behavior, pinned so the refactor didn't break the happy path."""

    def test_new_user_saves_api_key_from_poll(
        self, poll_responses, captured_saves
    ):
        script, used = poll_responses
        # Sequence: device-code create → poll approved with api_key
        script["post"] = [
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            (200, {"status": "approved", "api_key": "cue_sk_new_user_123", "email": "new@example.com"}),
        ]

        auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        assert len(captured_saves) == 1
        assert captured_saves[0]["data"]["api_key"] == "cue_sk_new_user_123"
        assert captured_saves[0]["data"]["email"] == "new@example.com"
        # Session exchange must NOT have been called — new user path
        # has the key inline.
        assert not any(c["path"] == "/auth/session" for c in used["post"])
        assert not any(c["path"] == "/auth/key" for c in used["get"])


class TestExistingUserDecryptSucceeded:
    """Server was able to decrypt the stored api_key_encrypted —
    poll returns api_key + existing_user=True."""

    def test_existing_user_with_inline_key_skips_session_exchange(
        self, poll_responses, captured_saves
    ):
        script, used = poll_responses
        script["post"] = [
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            (200, {
                "status": "approved",
                "api_key": "cue_sk_existing_decrypted",
                "email": "old@example.com",
                "existing_user": True,
                "session_token": "stk_abc",
            }),
        ]

        auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        assert captured_saves[0]["data"]["api_key"] == "cue_sk_existing_decrypted"
        # session_token is present in the poll response but we have the
        # key already — no need to hit /auth/session or /auth/key.
        assert not any(c["path"] == "/auth/session" for c in used["post"])
        assert not any(c["path"] == "/auth/key" for c in used["get"])


class TestExistingUserNeedsSessionExchange:
    """Server couldn't decrypt — poll omits api_key. CLI must exchange
    session_token for JWT, then call GET /v1/auth/key."""

    def test_falls_back_to_session_exchange_then_reveal(
        self, poll_responses, captured_saves
    ):
        script, used = poll_responses
        script["post"] = [
            # create device code
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            # poll approved — no api_key, but session_token present
            (200, {
                "status": "approved",
                "email": "existing@example.com",
                "session_token": "stk_one_time",
                "existing_user": True,
            }),
            # /auth/session → JWT
            (200, {"session_token": "jwt_payload_here", "email": "existing@example.com"}),
        ]
        script["get"] = [
            # /auth/key with Bearer jwt → api_key
            (200, {"api_key": "cue_sk_revealed_via_jwt"}),
        ]

        auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        # Session exchange happened with the single-use token.
        session_calls = [c for c in used["post"] if c["path"] == "/auth/session"]
        assert len(session_calls) == 1
        assert session_calls[0]["json"]["token"] == "stk_one_time"

        # /auth/key was called with the JWT as Bearer.
        reveal_calls = [c for c in used["get"] if c["path"] == "/auth/key"]
        assert len(reveal_calls) == 1
        assert reveal_calls[0]["headers"]["Authorization"] == "Bearer jwt_payload_here"

        # Saved the revealed key, not the session_token.
        assert captured_saves[0]["data"]["api_key"] == "cue_sk_revealed_via_jwt"


class TestFailureModes:
    """echo_error in cueapi.formatting raises SystemExit(1), so these
    failure-path tests wrap do_login in pytest.raises(SystemExit) and
    read the actionable message from stderr (not stdout)."""

    def test_reveal_returns_410_shows_regenerate_hint(
        self, poll_responses, captured_saves, capsys
    ):
        """plaintext_unavailable (410) must be translated into a clear
        "run cueapi key regenerate" message, not a cryptic stacktrace."""
        script, used = poll_responses
        script["post"] = [
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            (200, {"status": "approved", "email": "gone@example.com",
                   "session_token": "stk_x", "existing_user": True}),
            (200, {"session_token": "jwt_x", "email": "gone@example.com"}),
        ]
        script["get"] = [(410, {"error": {"code": "plaintext_unavailable"}})]

        with pytest.raises(SystemExit):
            auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        assert captured_saves == []
        err = capsys.readouterr().err
        assert "cueapi key regenerate" in err

    def test_session_exchange_failure_surfaces_error(
        self, poll_responses, captured_saves, capsys
    ):
        script, used = poll_responses
        script["post"] = [
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            (200, {"status": "approved", "email": "x@example.com",
                   "session_token": "stk_x", "existing_user": True}),
            # /auth/session fails
            (500, {"error": {"code": "session_unavailable"}}),
        ]

        with pytest.raises(SystemExit):
            auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        assert captured_saves == []
        err = capsys.readouterr().err
        assert "500" in err or "try again" in err.lower()

    def test_approved_without_any_key_or_token_shows_actionable_error(
        self, poll_responses, captured_saves, capsys
    ):
        """Defensive: if the server returns neither api_key nor
        session_token we don't crash — we tell the user what to do."""
        script, used = poll_responses
        script["post"] = [
            (201, {"verification_url": "https://example/verify", "expires_in": 60}),
            (200, {"status": "approved", "email": "x@example.com"}),
        ]

        with pytest.raises(SystemExit):
            auth.do_login(api_base="https://api.cueapi.ai/v1", profile="default")

        assert captured_saves == []
        err = capsys.readouterr().err
        assert "api_key" in err or "session_token" in err or "support" in err
