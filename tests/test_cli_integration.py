"""Integration tests for cueapi CLI → API contract.

Before this file existed, test_cli.py only validated argument parsing
and help text — zero tests exercised the HTTP call the CLI makes.
A breaking change in cueapi-core or the SDK could land without
cueapi-cli's CI catching it.

These tests patch cueapi.cli.CueAPIClient so the real httpx stack
isn't exercised. What we verify is the mapping from user-facing
CLI flags to the request body/path/params that would go on the wire.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cueapi.cli import main

runner = CliRunner()

# Test API key that bypasses credential file lookup. Shape matches
# the validator but points at no real account.
FAKE_KEY = "cue_sk_" + "a" * 32


def _make_client_mock(status_code: int = 201, body: dict | None = None) -> MagicMock:
    """Build a mock that mimics `with CueAPIClient(...) as client: ...`.

    Returns (client_class_mock, client_instance_mock). The instance
    mock is what the test inspects for the HTTP call assertion.
    """
    client_instance = MagicMock()
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body or {}
    for method in ("get", "post", "patch", "delete"):
        getattr(client_instance, method).return_value = response
    client_class = MagicMock()
    client_class.return_value.__enter__.return_value = client_instance
    client_class.return_value.__exit__.return_value = None
    return client_class, client_instance


class TestCreate:
    def test_recurring_posts_correct_body(self):
        client_class, client = _make_client_mock(
            status_code=201,
            body={"id": "cue_abc", "status": "active"},
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            result = runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "daily-sync",
                    "--cron", "0 9 * * *",
                    "--url", "https://example.com/hook",
                ],
            )
        assert result.exit_code == 0, result.output
        client.post.assert_called_once()
        path, = client.post.call_args.args
        body = client.post.call_args.kwargs["json"]
        assert path == "/cues"
        assert body["name"] == "daily-sync"
        assert body["schedule"] == {
            "type": "recurring",
            "cron": "0 9 * * *",
            "timezone": "UTC",
        }
        assert body["callback"] == {"url": "https://example.com/hook", "method": "POST"}

    def test_one_time_uses_once_schedule(self):
        client_class, client = _make_client_mock(
            status_code=201, body={"id": "cue_abc", "status": "active"}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "reminder",
                    "--at", "2026-05-01T14:00:00Z",
                    "--url", "https://example.com/notify",
                ],
            )
        body = client.post.call_args.kwargs["json"]
        assert body["schedule"] == {
            "type": "once",
            "at": "2026-05-01T14:00:00Z",
            "timezone": "UTC",
        }

    def test_worker_transport_omits_callback(self):
        client_class, client = _make_client_mock(
            status_code=201, body={"id": "cue_abc", "status": "active"}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "agent-task",
                    "--cron", "0 * * * *",
                    "--worker",
                ],
            )
        body = client.post.call_args.kwargs["json"]
        assert body["transport"] == "worker"
        assert "callback" not in body

    def test_payload_is_parsed_as_json(self):
        client_class, client = _make_client_mock(
            status_code=201, body={"id": "cue_abc", "status": "active"}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "t",
                    "--cron", "0 9 * * *",
                    "--url", "https://example.com",
                    "--payload", '{"task": "draft", "n": 3}',
                ],
            )
        body = client.post.call_args.kwargs["json"]
        assert body["payload"] == {"task": "draft", "n": 3}

    def test_on_failure_is_parsed_as_json(self):
        client_class, client = _make_client_mock(
            status_code=201, body={"id": "cue_abc", "status": "active"}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "t",
                    "--cron", "0 9 * * *",
                    "--url", "https://example.com",
                    "--on-failure", '{"after_attempts": 3, "notify": "ops@example.com"}',
                ],
            )
        body = client.post.call_args.kwargs["json"]
        assert body["on_failure"] == {
            "after_attempts": 3,
            "notify": "ops@example.com",
        }

    def test_invalid_payload_json_rejected_before_api_call(self):
        client_class, client = _make_client_mock()
        with patch("cueapi.cli.CueAPIClient", client_class):
            result = runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "t",
                    "--cron", "0 9 * * *",
                    "--url", "https://example.com",
                    "--payload", "{not json}",
                ],
            )
        assert result.exit_code != 0
        assert "valid json" in result.output.lower()
        client.post.assert_not_called()

    def test_403_surfaces_upgrade_hint(self):
        client_class, client = _make_client_mock(
            status_code=403,
            body={"detail": {"error": {"message": "Cue limit exceeded on free plan"}}},
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            result = runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "create",
                    "--name", "t",
                    "--cron", "0 9 * * *",
                    "--url", "https://example.com",
                ],
            )
        assert "cueapi upgrade" in result.output.lower()


class TestList:
    def test_defaults(self):
        client_class, client = _make_client_mock(
            status_code=200, body={"cues": [], "total": 0}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(main, ["--api-key", FAKE_KEY, "list"])
        client.get.assert_called_once()
        path, = client.get.call_args.args
        params = client.get.call_args.kwargs["params"]
        assert path == "/cues"
        assert params == {"limit": 20, "offset": 0}

    def test_with_filters(self):
        client_class, client = _make_client_mock(
            status_code=200, body={"cues": [], "total": 0}
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                [
                    "--api-key", FAKE_KEY,
                    "list",
                    "--status", "active",
                    "--limit", "50",
                    "--offset", "10",
                ],
            )
        params = client.get.call_args.kwargs["params"]
        assert params == {"status": "active", "limit": 50, "offset": 10}


class TestPauseResume:
    def test_pause_patches_correct_path(self):
        client_class, client = _make_client_mock(
            status_code=200,
            body={"id": "cue_abc", "name": "t", "status": "paused"},
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(main, ["--api-key", FAKE_KEY, "pause", "cue_abc"])
        path, = client.patch.call_args.args
        body = client.patch.call_args.kwargs["json"]
        assert path == "/cues/cue_abc"
        assert body == {"status": "paused"}

    def test_resume_sets_status_active(self):
        client_class, client = _make_client_mock(
            status_code=200,
            body={"id": "cue_abc", "name": "t", "status": "active"},
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(main, ["--api-key", FAKE_KEY, "resume", "cue_abc"])
        body = client.patch.call_args.kwargs["json"]
        assert body == {"status": "active"}


class TestUpdate:
    def test_update_name_only(self):
        client_class, client = _make_client_mock(
            status_code=200,
            body={"id": "cue_abc", "name": "renamed", "status": "active"},
        )
        with patch("cueapi.cli.CueAPIClient", client_class):
            runner.invoke(
                main,
                ["--api-key", FAKE_KEY, "update", "cue_abc", "--name", "renamed"],
            )
        path, = client.patch.call_args.args
        body = client.patch.call_args.kwargs["json"]
        assert path == "/cues/cue_abc"
        assert body == {"name": "renamed"}

    def test_update_requires_at_least_one_field(self):
        client_class, client = _make_client_mock()
        with patch("cueapi.cli.CueAPIClient", client_class):
            result = runner.invoke(
                main, ["--api-key", FAKE_KEY, "update", "cue_abc"]
            )
        assert result.exit_code != 0
        assert "at least one field" in result.output.lower()
        client.patch.assert_not_called()
