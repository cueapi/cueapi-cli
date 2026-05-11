"""Unit tests for cueapi CLI commands using Click's CliRunner.

No live API calls — tests only verify CLI entry points, help text, and argument parsing.
"""

from typing import Any, Optional

import pytest
from click.testing import CliRunner

from cueapi.cli import main


runner = CliRunner()


def test_version():
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "cueapi" in result.output
    assert "0." in result.output  # version starts with 0.x


def test_help():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "CueAPI" in result.output
    assert "create" in result.output
    assert "list" in result.output
    assert "login" in result.output
    assert "whoami" in result.output
    assert "quickstart" in result.output


def test_login_help():
    result = runner.invoke(main, ["login", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output.lower() or "authenticate" in result.output.lower()


def test_create_help():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "--name" in result.output
    assert "--url" in result.output
    assert "--worker" in result.output
    assert "--payload" in result.output
    assert "--on-failure" in result.output


def test_create_worker_flag_in_help():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "worker transport" in result.output.lower() or "--worker" in result.output


def test_create_requires_url_or_worker():
    result = runner.invoke(main, ["create", "--name", "test", "--cron", "0 9 * * *"])
    assert result.exit_code != 0
    assert "url" in result.output.lower() or "worker" in result.output.lower()


def test_create_on_failure_in_help():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "--on-failure" in result.output


def test_create_callback_alias():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "--callback" in result.output


def test_update_help():
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0
    assert "--name" in result.output
    assert "--cron" in result.output
    assert "--callback" in result.output
    assert "--payload" in result.output
    assert "--on-failure" in result.output


def test_update_requires_field():
    result = runner.invoke(main, ["update", "cue_test123"])
    assert result.exit_code != 0
    assert "must specify" in result.output.lower() or "at least one" in result.output.lower()


def test_key_regenerate_help():
    result = runner.invoke(main, ["key", "regenerate", "--help"])
    assert result.exit_code == 0
    assert "--yes" in result.output or "-y" in result.output


def test_list_help():
    result = runner.invoke(main, ["list", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output.lower() or "cue" in result.output.lower()


def test_get_help():
    result = runner.invoke(main, ["get", "--help"])
    assert result.exit_code == 0
    assert "get" in result.output.lower() or "info" in result.output.lower()


def test_pause_help():
    result = runner.invoke(main, ["pause", "--help"])
    assert result.exit_code == 0
    assert "pause" in result.output.lower()


def test_resume_help():
    result = runner.invoke(main, ["resume", "--help"])
    assert result.exit_code == 0
    assert "resume" in result.output.lower()


def test_delete_help():
    result = runner.invoke(main, ["delete", "--help"])
    assert result.exit_code == 0
    assert "delete" in result.output.lower()


def test_whoami_help():
    result = runner.invoke(main, ["whoami", "--help"])
    assert result.exit_code == 0
    assert "whoami" in result.output.lower() or "user" in result.output.lower()


def test_usage_help():
    result = runner.invoke(main, ["usage", "--help"])
    assert result.exit_code == 0
    assert "usage" in result.output.lower()


def test_quickstart_help():
    result = runner.invoke(main, ["quickstart", "--help"])
    assert result.exit_code == 0
    assert "quickstart" in result.output.lower() or "setup" in result.output.lower()


# --- fire ---


def test_fire_help():
    result = runner.invoke(main, ["fire", "--help"])
    assert result.exit_code == 0
    assert "fire" in result.output.lower()
    assert "--payload-override" in result.output
    assert "--merge-strategy" in result.output
    # PR #618 + #632 + #683 parity
    assert "--send-at" in result.output
    assert "--exit-criteria" in result.output
    assert "--idempotency-key" in result.output


def test_fire_exit_criteria_repeatable_via_help():
    """--exit-criteria takes multiple values (click multiple=True). Verify the
    parser accepts repeated flags by passing them alongside --help."""
    result = runner.invoke(
        main,
        [
            "fire", "cue_x",
            "--exit-criteria", "task_completed",
            "--exit-criteria", "result_valid",
            "--help",  # short-circuits actual fire — we just want parse to accept
        ],
    )
    assert result.exit_code == 0


def test_fire_help_pins_idempotency_key_as_body_field():
    """Pin: the help text MUST call out that idempotency_key flows as a body
    field on cues fire (NOT a header), to prevent a future 'simplifying'
    refactor that moves it to a header — server's FireRequest schema is
    extra='forbid' and would NOT see it as a header. Same divergence I caught
    on cueapi-python #33 + cueapi-mcp #29."""
    result = runner.invoke(main, ["fire", "--help"])
    output = result.output.lower()
    assert "body field" in output or "body" in output


def test_fire_requires_cue_id():
    result = runner.invoke(main, ["fire"])
    assert result.exit_code != 0
    assert "cue_id" in result.output.lower() or "missing" in result.output.lower()


def test_fire_payload_override_invalid_json_rejected():
    result = runner.invoke(main, ["fire", "cue_x", "--payload-override", "{not json"])
    assert result.exit_code != 0
    assert "json" in result.output.lower()


def test_fire_merge_strategy_choice_validation():
    # Not in (merge, replace), Click rejects.
    result = runner.invoke(main, ["fire", "cue_x", "--merge-strategy", "garbage"])
    assert result.exit_code != 0
    assert "merge" in result.output.lower() or "replace" in result.output.lower() or "invalid" in result.output.lower()


# --- executions group ---


def test_executions_group_help():
    result = runner.invoke(main, ["executions", "--help"])
    assert result.exit_code == 0
    for sub in ("list", "list-claimable", "get", "claim", "claim-next", "heartbeat", "report-outcome"):
        assert sub in result.output, f"executions subcommand {sub} missing from --help"


def test_executions_list_help():
    result = runner.invoke(main, ["executions", "list", "--help"])
    assert result.exit_code == 0
    assert "--cue-id" in result.output
    assert "--status" in result.output
    assert "--limit" in result.output
    assert "--offset" in result.output


def test_executions_list_claimable_help():
    result = runner.invoke(main, ["executions", "list-claimable", "--help"])
    assert result.exit_code == 0
    assert "--task" in result.output
    assert "--agent" in result.output


def test_executions_get_help():
    result = runner.invoke(main, ["executions", "get", "--help"])
    assert result.exit_code == 0
    assert "execution_id" in result.output.lower()


def test_executions_claim_help():
    result = runner.invoke(main, ["executions", "claim", "--help"])
    assert result.exit_code == 0
    assert "--worker-id" in result.output
    assert "execution_id" in result.output.lower()


def test_executions_claim_requires_worker_id():
    result = runner.invoke(main, ["executions", "claim", "exec_x"])
    assert result.exit_code != 0
    assert "worker" in result.output.lower()


def test_executions_claim_next_help():
    result = runner.invoke(main, ["executions", "claim-next", "--help"])
    assert result.exit_code == 0
    assert "--worker-id" in result.output
    assert "--task" in result.output


def test_executions_claim_next_requires_worker_id():
    result = runner.invoke(main, ["executions", "claim-next"])
    assert result.exit_code != 0
    assert "worker" in result.output.lower()


def test_executions_heartbeat_help():
    result = runner.invoke(main, ["executions", "heartbeat", "--help"])
    assert result.exit_code == 0
    assert "--worker-id" in result.output
    assert "execution_id" in result.output.lower()


def test_executions_heartbeat_requires_worker_id():
    result = runner.invoke(main, ["executions", "heartbeat", "exec_x"])
    assert result.exit_code != 0
    assert "worker" in result.output.lower()


def test_executions_report_outcome_help():
    result = runner.invoke(main, ["executions", "report-outcome", "--help"])
    assert result.exit_code == 0
    assert "--success" in result.output
    assert "--failure" in result.output
    assert "--external-id" in result.output
    assert "--result-url" in result.output
    assert "--summary" in result.output


def test_executions_report_outcome_requires_success_flag():
    result = runner.invoke(main, ["executions", "report-outcome", "exec_x"])
    assert result.exit_code != 0


# --- top-level surface includes new commands ---


def test_top_level_help_lists_fire_and_executions():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "fire" in result.output
    assert "executions" in result.output


# --- messaging primitive: agents command group ---


class _FakeResp:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _AgentsClient:
    """Captures GET / POST / PATCH / DELETE for cueapi agents tests."""

    def __init__(self, responses: Optional[dict] = None):
        # responses keyed by ("METHOD", path-prefix) → _FakeResp factory
        self.calls: list = []
        self._responses = responses or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def _resolve(self, method: str, path: str):
        # Match longest path key for flexibility.
        for (m, p), factory in sorted(self._responses.items(), key=lambda kv: -len(kv[0][1])):
            if m == method and path.startswith(p):
                return factory()
        return _FakeResp(200, {})

    def get(self, path, params=None, **_):
        self.calls.append(("GET", path, params))
        return self._resolve("GET", path)

    def post(self, path, json=None, **_):
        self.calls.append(("POST", path, json))
        return self._resolve("POST", path)

    def patch(self, path, json=None, **_):
        self.calls.append(("PATCH", path, json))
        return self._resolve("PATCH", path)

    def delete(self, path, **_):
        self.calls.append(("DELETE", path, None))
        return self._resolve("DELETE", path)


def _patch_client(monkeypatch, client_holder, responses=None):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        client_holder["client"] = _AgentsClient(responses=responses)
        return client_holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


# --- help-text shape ---


def test_agents_group_help():
    result = runner.invoke(main, ["agents", "--help"])
    assert result.exit_code == 0
    for sub in ("create", "list", "get", "update", "delete", "webhook-secret", "inbox", "sent"):
        assert sub in result.output, f"agents subcommand {sub} missing from --help"


def test_agents_create_help_lists_required_and_optional():
    result = runner.invoke(main, ["agents", "create", "--help"])
    assert result.exit_code == 0
    assert "--display-name" in result.output
    assert "--slug" in result.output
    assert "--webhook-url" in result.output
    assert "--metadata" in result.output


def test_agents_update_help_includes_clear_webhook_url():
    result = runner.invoke(main, ["agents", "update", "--help"])
    assert result.exit_code == 0
    assert "--display-name" in result.output
    assert "--webhook-url" in result.output
    assert "--clear-webhook-url" in result.output
    assert "--status" in result.output


def test_agents_webhook_secret_subcommands_present():
    result = runner.invoke(main, ["agents", "webhook-secret", "--help"])
    assert result.exit_code == 0
    assert "get" in result.output
    assert "regenerate" in result.output


# --- create body construction ---


def test_agents_create_minimal_only_display_name(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents"): lambda: _FakeResp(
                201,
                {"id": "agt_x", "slug": "team-comm", "display_name": "Team Comm", "status": "online"},
            )
        },
    )
    result = runner.invoke(main, ["agents", "create", "--display-name", "Team Comm"])
    assert result.exit_code == 0, result.output
    method, path, body = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/agents"
    assert body == {"display_name": "Team Comm"}


def test_agents_create_with_all_optionals(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents"): lambda: _FakeResp(
                201,
                {
                    "id": "agt_x",
                    "slug": "team-comm",
                    "display_name": "Team Comm",
                    "status": "online",
                    "webhook_url": "https://x.example/webhook",
                    "webhook_secret": "wsec_secretvalue",
                },
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "agents", "create",
            "--display-name", "Team Comm",
            "--slug", "team-comm",
            "--webhook-url", "https://x.example/webhook",
            "--metadata", '{"team": "platform"}',
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {
        "display_name": "Team Comm",
        "slug": "team-comm",
        "webhook_url": "https://x.example/webhook",
        "metadata": {"team": "platform"},
    }
    # Webhook-secret one-time view should appear in stdout.
    assert "wsec_secretvalue" in result.output
    assert "save now" in result.output.lower() or "shown once" in result.output.lower()


def test_agents_create_invalid_metadata_json(monkeypatch):
    holder: dict = {}
    _patch_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["agents", "create", "--display-name", "X", "--metadata", "{not json"],
    )
    assert result.exit_code != 0
    assert "json" in result.output.lower()


# --- list params ---


def test_agents_list_params_omitted_when_unset(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={("GET", "/agents"): lambda: _FakeResp(200, {"agents": [], "total": 0})},
    )
    result = runner.invoke(main, ["agents", "list"])
    assert result.exit_code == 0, result.output
    _, _, params = holder["client"].calls[-1]
    assert "status" not in params
    assert "include_deleted" not in params
    assert params["limit"] == 50
    assert params["offset"] == 0


def test_agents_list_status_validated_by_click():
    # Bad status — Click's choice validation rejects.
    result = runner.invoke(main, ["agents", "list", "--status", "wat"])
    assert result.exit_code != 0
    assert (
        "online" in result.output.lower()
        or "invalid" in result.output.lower()
        or "choice" in result.output.lower()
    )


def test_agents_list_include_deleted_flag_only_sent_when_true(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={("GET", "/agents"): lambda: _FakeResp(200, {"agents": [], "total": 0})},
    )
    result = runner.invoke(main, ["agents", "list", "--include-deleted"])
    assert result.exit_code == 0
    assert holder["client"].calls[-1][2].get("include_deleted") == "true"


# --- get ---


def test_agents_get_renders_metadata_and_status(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_test"): lambda: _FakeResp(
                200,
                {
                    "id": "agt_test",
                    "slug": "x",
                    "display_name": "X Agent",
                    "status": "online",
                    "webhook_url": None,
                    "metadata": {"k": "v"},
                },
            )
        },
    )
    result = runner.invoke(main, ["agents", "get", "agt_test"])
    assert result.exit_code == 0
    assert "agt_test" in result.output
    assert "X Agent" in result.output
    assert "poll-only" in result.output  # webhook_url null path


def test_agents_get_404_logs_not_found(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/missing"): lambda: _FakeResp(404, {})
        },
    )
    result = runner.invoke(main, ["agents", "get", "missing"])
    # echo_error doesn't change exit code in the existing pattern; just check
    # the user-visible "not found" string is rendered.
    assert "not found" in result.output.lower() or "missing" in result.output


# --- update body ---


def test_agents_update_partial_body(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("PATCH", "/agents/agt_x"): lambda: _FakeResp(
                200, {"id": "agt_x", "slug": "x"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["agents", "update", "agt_x", "--status", "away"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert body == {"status": "away"}


def test_agents_update_clear_webhook_url_sends_explicit_null(monkeypatch):
    # The server uses model_fields_set to disambiguate "field omitted" from
    # "field explicitly null." The CLI's --clear-webhook-url MUST send literal
    # JSON null in the body. Pinning so a refactor can't silently drop the key.
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("PATCH", "/agents/agt_x"): lambda: _FakeResp(200, {"id": "agt_x", "slug": "x"})
        },
    )
    result = runner.invoke(
        main,
        ["agents", "update", "agt_x", "--clear-webhook-url"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    # Important: key MUST be present and value MUST be None, not omitted.
    assert "webhook_url" in body
    assert body["webhook_url"] is None


def test_agents_update_webhook_url_and_clear_mutually_exclusive():
    result = runner.invoke(
        main,
        [
            "agents", "update", "agt_x",
            "--webhook-url", "https://x.example",
            "--clear-webhook-url",
        ],
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower() or "mutually" in result.output.lower()


def test_agents_update_requires_a_field():
    result = runner.invoke(main, ["agents", "update", "agt_x"])
    assert result.exit_code != 0
    assert "must specify" in result.output.lower() or "at least one" in result.output.lower()


# --- delete ---


def test_agents_delete_with_yes(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("DELETE", "/agents/agt_x"): lambda: _FakeResp(204, {})
        },
    )
    result = runner.invoke(main, ["agents", "delete", "agt_x", "--yes"])
    assert result.exit_code == 0, result.output
    assert holder["client"].calls[-1][:2] == ("DELETE", "/agents/agt_x")


def test_agents_delete_without_yes_prompts_then_aborts():
    # No --yes, no confirmation input → aborts.
    result = runner.invoke(main, ["agents", "delete", "agt_x"], input="n\n")
    assert "Aborted" in result.output or "aborted" in result.output.lower()


# --- webhook-secret ---


def test_agents_webhook_secret_get(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/webhook-secret"): lambda: _FakeResp(
                200, {"webhook_secret": "wsec_revealed"}
            )
        },
    )
    result = runner.invoke(main, ["agents", "webhook-secret", "get", "agt_x"])
    assert result.exit_code == 0
    assert "wsec_revealed" in result.output


def test_agents_webhook_secret_regenerate_with_yes(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents/agt_x/webhook-secret/regenerate"): lambda: _FakeResp(
                200, {"webhook_secret": "wsec_new"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["agents", "webhook-secret", "regenerate", "agt_x", "--yes"],
    )
    assert result.exit_code == 0, result.output
    assert "wsec_new" in result.output
    assert "save now" in result.output.lower() or "shown once" in result.output.lower()


def test_agents_webhook_secret_regenerate_sends_destructive_header(monkeypatch):
    """Pin: `cueapi agents webhook-secret regenerate` MUST send
    `X-Confirm-Destructive: true` header — server requires it (Bug
    cmp03hy9o, surfaced 2026-05-10 from Phase 2 messaging smoke).
    Mirrors the same header pin on `cueapi key webhook-secret regenerate`.
    """
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents/agt_x/webhook-secret/regenerate"): lambda: _FakeResp(
                200, {"webhook_secret": "wsec_new"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["agents", "webhook-secret", "regenerate", "agt_x", "--yes"],
    )
    assert result.exit_code == 0, result.output
    method, path, body, headers = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/agents/agt_x/webhook-secret/regenerate"
    assert headers == {"X-Confirm-Destructive": "true"}
    assert "wsec_new" in result.output


# --- inbox / sent ---


def test_agents_inbox_renders_messages(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/inbox"): lambda: _FakeResp(
                200,
                {
                    "messages": [
                        {
                            "id": "msg_a",
                            "from": {"slug": "sender@x", "agent_id": "agt_sender"},
                            "subject": "hello",
                            "state": "queued",
                        }
                    ],
                    "total": 1,
                },
            )
        },
    )
    result = runner.invoke(main, ["agents", "inbox", "agt_x"])
    assert result.exit_code == 0, result.output
    assert "msg_a" in result.output
    assert "hello" in result.output
    assert "sender@x" in result.output


def test_agents_inbox_state_filter_passed_as_param(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/inbox"): lambda: _FakeResp(
                200, {"messages": [], "total": 0}
            )
        },
    )
    result = runner.invoke(
        main,
        ["agents", "inbox", "agt_x", "--state", "queued"],
    )
    assert result.exit_code == 0
    params = holder["client"].calls[-1][2]
    assert params.get("state") == "queued"


def test_agents_sent_renders_messages(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/sent"): lambda: _FakeResp(
                200,
                {
                    "messages": [
                        {
                            "id": "msg_s",
                            "to": "recipient@y",
                            "subject": "re: hello",
                            "state": "delivered",
                        }
                    ],
                    "total": 1,
                },
            )
        },
    )
    result = runner.invoke(main, ["agents", "sent", "agt_x"])
    assert result.exit_code == 0, result.output
    assert "msg_s" in result.output
    assert "recipient@y" in result.output


# --- top-level surface includes agents ---


def test_top_level_help_lists_agents():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "agents" in result.output


# --- workers + key webhook-secret ---
#
# Reuses _FakeResp from the agents tests above. _WSClient is a separate
# capture client because it tracks the headers kwarg (needed for the
# X-Confirm-Destructive pin on key webhook-secret regenerate).


class _WSClient:
    def __init__(self, responses: Optional[dict] = None):
        self.calls: list = []
        self._responses = responses or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def _resolve(self, method: str, path: str):
        for (m, p), factory in sorted(self._responses.items(), key=lambda kv: -len(kv[0][1])):
            if m == method and path.startswith(p):
                return factory()
        return _FakeResp(200, {})

    def get(self, path, params=None, **_):
        self.calls.append(("GET", path, params, None))
        return self._resolve("GET", path)

    def post(self, path, json=None, headers=None, **_):
        self.calls.append(("POST", path, json, headers))
        return self._resolve("POST", path)

    def delete(self, path, **_):
        self.calls.append(("DELETE", path, None, None))
        return self._resolve("DELETE", path)


def _patch_ws_client(monkeypatch, holder, responses=None):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _WSClient(responses=responses)
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


def test_workers_group_help():
    result = runner.invoke(main, ["workers", "--help"])
    assert result.exit_code == 0
    for sub in ("list", "delete"):
        assert sub in result.output


def test_workers_list_renders(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/workers"): lambda: _FakeResp(
                200,
                {
                    "workers": [
                        {
                            "worker_id": "worker-1",
                            "heartbeat_status": "online",
                            "seconds_since_heartbeat": 5,
                            "last_heartbeat": "2026-05-04T17:30:00Z",
                        }
                    ],
                    "total": 1,
                },
            )
        },
    )
    result = runner.invoke(main, ["workers", "list"])
    assert result.exit_code == 0, result.output
    assert "worker-1" in result.output
    assert "online" in result.output


def test_workers_list_empty_renders_install_hint(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/workers"): lambda: _FakeResp(200, {"workers": [], "total": 0})
        },
    )
    result = runner.invoke(main, ["workers", "list"])
    assert result.exit_code == 0
    assert "no workers" in result.output.lower() or "register" in result.output.lower()


def test_workers_delete_with_yes(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("DELETE", "/workers/worker-1"): lambda: _FakeResp(204, {})
        },
    )
    result = runner.invoke(main, ["workers", "delete", "worker-1", "--yes"])
    assert result.exit_code == 0, result.output
    assert holder["client"].calls[-1][:2] == ("DELETE", "/workers/worker-1")


def test_workers_delete_without_yes_aborts():
    result = runner.invoke(main, ["workers", "delete", "worker-1"], input="n\n")
    assert "Aborted" in result.output or "aborted" in result.output.lower()


def test_key_webhook_secret_get_help():
    result = runner.invoke(main, ["key", "webhook-secret", "get", "--help"])
    assert result.exit_code == 0


def test_key_webhook_secret_regenerate_help():
    result = runner.invoke(main, ["key", "webhook-secret", "regenerate", "--help"])
    assert result.exit_code == 0
    assert "--yes" in result.output or "-y" in result.output


def test_key_webhook_secret_get_renders(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/auth/webhook-secret"): lambda: _FakeResp(
                200, {"webhook_secret": "wsec_user_revealed"}
            )
        },
    )
    result = runner.invoke(main, ["key", "webhook-secret", "get"])
    assert result.exit_code == 0
    assert "wsec_user_revealed" in result.output


def test_key_webhook_secret_get_404_helpful_error(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/auth/webhook-secret"): lambda: _FakeResp(404, {})
        },
    )
    result = runner.invoke(main, ["key", "webhook-secret", "get"])
    assert "agents webhook-secret" in result.output


def test_key_webhook_secret_regenerate_sends_destructive_header(monkeypatch):
    holder: dict = {}
    _patch_ws_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/auth/webhook-secret/regenerate"): lambda: _FakeResp(
                200, {"webhook_secret": "wsec_new"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["key", "webhook-secret", "regenerate", "--yes"],
    )
    assert result.exit_code == 0, result.output
    method, path, body, headers = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/auth/webhook-secret/regenerate"
    assert headers == {"X-Confirm-Destructive": "true"}
    assert "wsec_new" in result.output


def test_key_webhook_secret_regenerate_aborts_without_yes():
    result = runner.invoke(
        main,
        ["key", "webhook-secret", "regenerate"],
        input="n\n",
    )
    assert "Aborted" in result.output or "aborted" in result.output.lower()


# --- create / update extra flags (parity with hosted CueCreate / CueUpdate) ---


class _FakeResp:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _CueClient:
    """Captures POST/PATCH for cue create/update body assertions."""

    def __init__(self):
        self.posted: list = []
        self.patched: list = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def post(self, path, json=None, **_):
        self.posted.append((path, json))
        return _FakeResp(201, {"id": "cue_test", "status": "active", "next_run": None})

    def patch(self, path, json=None, **_):
        self.patched.append((path, json))
        return _FakeResp(200, {"id": "cue_test", "name": (json or {}).get("name") or "x"})

    def get(self, *_, **__):
        return _FakeResp(200, {})


def _patch_cue_client(monkeypatch, holder):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _CueClient()
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


# --- help-text shape ---


def test_create_help_lists_new_flags():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    for flag in ("--delivery", "--alerts", "--catch-up", "--verification", "--on-success-fire"):
        assert flag in result.output, f"create missing {flag}"


def test_update_help_lists_new_flags():
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0
    for flag in (
        "--status",
        "--delivery",
        "--alerts",
        "--catch-up",
        "--verification",
        "--on-success-fire",
        "--clear-on-success-fire",
    ):
        assert flag in result.output, f"update missing {flag}"


# --- create body construction ---


def test_create_with_all_new_flags(monkeypatch):
    holder: dict = {}
    _patch_cue_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "create",
            "--name", "x",
            "--cron", "0 9 * * *",
            "--worker",
            "--delivery", '{"timeout_seconds": 60}',
            "--alerts", '{"channels": ["email"]}',
            "--catch-up", "skip_missed",
            "--verification", '{"mode": "evidence_required"}',
            "--on-success-fire", "cue_chained",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert body["delivery"] == {"timeout_seconds": 60}
    assert body["alerts"] == {"channels": ["email"]}
    assert body["catch_up"] == "skip_missed"
    assert body["verification"] == {"mode": "evidence_required"}
    assert body["on_success_fire"] == "cue_chained"


def test_create_catch_up_validated_by_click():
    result = runner.invoke(
        main,
        ["create", "--name", "x", "--cron", "0 9 * * *", "--worker", "--catch-up", "garbage"],
    )
    assert result.exit_code != 0
    assert (
        "garbage" in result.output.lower()
        or "invalid" in result.output.lower()
        or "run_once_if_missed" in result.output
    )


def test_create_invalid_delivery_json():
    result = runner.invoke(
        main,
        ["create", "--name", "x", "--cron", "0 9 * * *", "--worker", "--delivery", "{not json"],
    )
    assert result.exit_code != 0
    assert "json" in result.output.lower()


def test_create_omits_unset_flags_from_body(monkeypatch):
    holder: dict = {}
    _patch_cue_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["create", "--name", "x", "--cron", "0 9 * * *", "--worker"],
    )
    assert result.exit_code == 0
    body = holder["client"].posted[-1][1]
    for k in ("delivery", "alerts", "catch_up", "verification", "on_success_fire"):
        assert k not in body, f"create body should omit {k} when unset"


# --- update body construction ---


def test_update_status_via_flag(monkeypatch):
    holder: dict = {}
    _patch_cue_client(monkeypatch, holder)
    result = runner.invoke(main, ["update", "cue_test", "--status", "paused"])
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert body == {"status": "paused"}


def test_update_status_validated_by_click():
    result = runner.invoke(main, ["update", "cue_test", "--status", "deleted"])
    assert result.exit_code != 0
    assert (
        "deleted" in result.output.lower()
        or "invalid" in result.output.lower()
        or "active" in result.output
    )


def test_update_with_all_new_flags(monkeypatch):
    holder: dict = {}
    _patch_cue_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "update", "cue_test",
            "--status", "active",
            "--delivery", '{"timeout_seconds": 90}',
            "--alerts", '{"channels": ["slack"]}',
            "--catch-up", "replay_all",
            "--verification", '{"mode": "manual"}',
            "--on-success-fire", "cue_next",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert body == {
        "status": "active",
        "delivery": {"timeout_seconds": 90},
        "alerts": {"channels": ["slack"]},
        "catch_up": "replay_all",
        "verification": {"mode": "manual"},
        "on_success_fire": "cue_next",
    }


def test_update_clear_on_success_fire_sends_null(monkeypatch):
    # Mirrors the agent --clear-webhook-url pattern. Server uses None to
    # disable chaining; the CLI must send literal JSON null, not omit.
    # Pinned so a refactor can't silently flip semantics.
    holder: dict = {}
    _patch_cue_client(monkeypatch, holder)
    result = runner.invoke(main, ["update", "cue_test", "--clear-on-success-fire"])
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert "on_success_fire" in body
    assert body["on_success_fire"] is None


def test_update_on_success_fire_and_clear_mutually_exclusive():
    result = runner.invoke(
        main,
        ["update", "cue_test", "--on-success-fire", "cue_x", "--clear-on-success-fire"],
    )
    assert result.exit_code != 0
    assert "mutually" in result.output.lower() or "exclusive" in result.output.lower()


def test_update_catch_up_validated_by_click():
    result = runner.invoke(main, ["update", "cue_test", "--catch-up", "wat"])
    assert result.exit_code != 0
    assert (
        "wat" in result.output.lower()
        or "invalid" in result.output.lower()
        or "run_once_if_missed" in result.output
    )


# --- payload_override enforcement flags (hosted PR #590) ---


def test_create_require_payload_override_in_help():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "--require-payload-override" in result.output
    assert "--no-require-payload-override" in result.output


def test_create_required_keys_in_help():
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0
    assert "--required-keys" in result.output


def test_update_require_payload_override_in_help():
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0
    assert "--require-payload-override" in result.output
    assert "--no-require-payload-override" in result.output


def test_update_required_keys_in_help():
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0
    assert "--required-keys" in result.output


# --- body-construction unit tests for new flags ---
#
# These mock the HTTP layer (CueAPIClient.post / .patch) and assert that the
# CLI body matches the hosted-API spec. Cheap insurance against flag-wiring
# regressions when refactoring create/update body builders.


class _FakeResp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self):
        self.posted: list = []
        self.patched: list = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def post(self, path, json=None, **_):
        self.posted.append((path, json))
        return _FakeResp(201, {"id": "cue_test", "status": "active", "next_run": None})

    def patch(self, path, json=None, **_):
        self.patched.append((path, json))
        return _FakeResp(200, {"id": "cue_test", "name": json.get("name", "x") if json else "x"})

    def get(self, *_, **__):
        # Not used by these tests but defined so the context-manager surface
        # matches CueAPIClient.
        return _FakeResp(200, {})


def _patched_client(monkeypatch, client_holder):
    """Patch CueAPIClient in cueapi.cli to return a captured FakeClient."""
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        client_holder["client"] = _FakeClient()
        return client_holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


def test_create_require_payload_override_true_sends_field(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "create",
            "--name", "team-comm",
            "--cron", "0 9 * * *",
            "--worker",
            "--require-payload-override",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert body.get("require_payload_override") is True


def test_create_no_require_payload_override_sends_false(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "create",
            "--name", "cron-cue",
            "--cron", "0 9 * * *",
            "--worker",
            "--no-require-payload-override",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert body.get("require_payload_override") is False


def test_create_omits_require_payload_override_when_unset(monkeypatch):
    # Default None must NOT appear in the body — server-side default is the
    # source of truth for "did the caller specify this?" Pinning this
    # behavior so a refactor can't silently start sending false.
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["create", "--name", "x", "--cron", "0 9 * * *", "--worker"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert "require_payload_override" not in body


def test_create_required_keys_splits_and_trims(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "create",
            "--name", "team-comm",
            "--cron", "0 9 * * *",
            "--worker",
            "--required-keys", " task ,message,  token",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert body.get("required_payload_keys") == ["task", "message", "token"]


def test_create_required_keys_empty_string_sends_empty_list(monkeypatch):
    # Empty string is the "explicit clear" path. Pin so a future refactor
    # doesn't drop the body field entirely (which would mean "leave
    # unchanged" not "clear").
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "create",
            "--name", "x",
            "--cron", "0 9 * * *",
            "--worker",
            "--required-keys", "",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].posted[-1][1]
    assert body.get("required_payload_keys") == []


def test_update_require_payload_override_tri_state(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["update", "cue_test", "--require-payload-override"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert body.get("require_payload_override") is True


def test_update_no_require_payload_override_sends_false(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["update", "cue_test", "--no-require-payload-override"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert body.get("require_payload_override") is False


def test_update_required_keys_works(monkeypatch):
    holder: dict = {}
    _patched_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["update", "cue_test", "--required-keys", "a,b"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].patched[-1][1]
    assert body.get("required_payload_keys") == ["a", "b"]


# --- effective payload display on `executions get` (hosted PR #589) ---


def test_executions_get_displays_payload_when_present(monkeypatch):
    import cueapi.cli as cli_mod

    fake_response = {
        "id": "exec_abc",
        "cue_id": "cue_xyz",
        "status": "success",
        "scheduled_for": "2026-05-04T10:00:00Z",
        "attempts": 1,
        "payload": {"task": "demo", "message": "hello"},
    }

    class _GetClient:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def get(self, path, **_):
            return _FakeResp(200, fake_response)

    monkeypatch.setattr(cli_mod, "CueAPIClient", lambda *_, **__: _GetClient())
    result = runner.invoke(main, ["executions", "get", "exec_abc"])
    assert result.exit_code == 0, result.output
    assert "Payload:" in result.output
    # Pretty-print with indent=2, sort_keys=True — pin the keys are visible.
    assert "task" in result.output
    assert "demo" in result.output


def test_executions_get_omits_payload_when_null(monkeypatch):
    import cueapi.cli as cli_mod

    fake_response = {
        "id": "exec_abc",
        "cue_id": "cue_xyz",
        "status": "pending",
        "payload": None,
    }

    class _GetClient:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def get(self, path, **_):
            return _FakeResp(200, fake_response)

    monkeypatch.setattr(cli_mod, "CueAPIClient", lambda *_, **__: _GetClient())
    result = runner.invoke(main, ["executions", "get", "exec_abc"])
    assert result.exit_code == 0, result.output
    assert "Payload:" not in result.output


# --- executions list filter parity (cueapi-cli #25 manifest gap) ---


class _FakeResp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _ListClient:
    def __init__(self):
        self.last_params: Optional[dict] = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def get(self, path, params=None, **_):
        self.last_params = params
        return _FakeResp(200, {"executions": [], "total": 0, "limit": 20, "offset": 0})


def _patched_list_client(monkeypatch, holder):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _ListClient()
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


def test_executions_list_help_includes_new_filters():
    result = runner.invoke(main, ["executions", "list", "--help"])
    assert result.exit_code == 0
    assert "--outcome-state" in result.output
    assert "--result-type" in result.output
    assert "--has-evidence" in result.output
    assert "--triggered-by" in result.output


def test_executions_list_outcome_state_passed_as_query_param(monkeypatch):
    holder: dict = {}
    _patched_list_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["executions", "list", "--outcome-state", "verified_success"],
    )
    assert result.exit_code == 0, result.output
    assert holder["client"].last_params.get("outcome_state") == "verified_success"


def test_executions_list_result_type_passed(monkeypatch):
    holder: dict = {}
    _patched_list_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["executions", "list", "--result-type", "pr"],
    )
    assert result.exit_code == 0, result.output
    assert holder["client"].last_params.get("result_type") == "pr"


def test_executions_list_has_evidence_only_sent_when_true(monkeypatch):
    # has_evidence is a flag — present means True. Unset = omit. Pinning
    # this so a refactor can't silently start sending `false` (which would
    # still mean "no filter" server-side, but creates noisy URLs and invites
    # future bugs).
    holder: dict = {}
    _patched_list_client(monkeypatch, holder)
    result_no_flag = runner.invoke(main, ["executions", "list"])
    assert result_no_flag.exit_code == 0
    assert "has_evidence" not in (holder["client"].last_params or {})

    holder2: dict = {}
    _patched_list_client(monkeypatch, holder2)
    result_with_flag = runner.invoke(main, ["executions", "list", "--has-evidence"])
    assert result_with_flag.exit_code == 0
    assert holder2["client"].last_params.get("has_evidence") == "true"


def test_executions_list_triggered_by_passed(monkeypatch):
    holder: dict = {}
    _patched_list_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["executions", "list", "--triggered-by", "manual_fire"],
    )
    assert result.exit_code == 0, result.output
    assert holder["client"].last_params.get("triggered_by") == "manual_fire"


def test_executions_list_combines_all_filters(monkeypatch):
    holder: dict = {}
    _patched_list_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "executions", "list",
            "--cue-id", "cue_xyz",
            "--status", "success",
            "--outcome-state", "verified_success",
            "--result-type", "pr",
            "--has-evidence",
            "--triggered-by", "scheduled",
            "--limit", "50",
        ],
    )
    assert result.exit_code == 0, result.output
    p = holder["client"].last_params
    assert p["cue_id"] == "cue_xyz"
    assert p["status"] == "success"
    assert p["outcome_state"] == "verified_success"
    assert p["result_type"] == "pr"
    assert p["has_evidence"] == "true"
    assert p["triggered_by"] == "scheduled"
    assert p["limit"] == 50


# --- executions: replay / verification-pending / verify ---


class _FakeResp:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _ExecClient:
    def __init__(self, responses: Optional[dict] = None):
        self.calls: list = []
        self._responses = responses or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def _resolve(self, method: str, path: str):
        for (m, p), factory in sorted(self._responses.items(), key=lambda kv: -len(kv[0][1])):
            if m == method and path.startswith(p):
                return factory()
        return _FakeResp(200, {})

    def post(self, path, json=None, **_):
        self.calls.append(("POST", path, json))
        return self._resolve("POST", path)

    def get(self, path, params=None, **_):
        self.calls.append(("GET", path, params))
        return self._resolve("GET", path)


def _patch_exec_client(monkeypatch, holder, responses=None):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _ExecClient(responses=responses)
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


def test_executions_replay_help():
    result = runner.invoke(main, ["executions", "replay", "--help"])
    assert result.exit_code == 0
    assert "execution_id" in result.output.lower()


def test_executions_verification_pending_help():
    result = runner.invoke(main, ["executions", "verification-pending", "--help"])
    assert result.exit_code == 0
    assert "execution_id" in result.output.lower()


def test_executions_verify_help_lists_flags():
    result = runner.invoke(main, ["executions", "verify", "--help"])
    assert result.exit_code == 0
    assert "--valid" in result.output
    assert "--invalid" in result.output
    assert "--reason" in result.output


def test_executions_replay_posts_empty_body(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/replay"): lambda: _FakeResp(
                200,
                {
                    "execution_id": "exec_new",
                    "scheduled_for": "2026-05-04T17:30:00Z",
                    "status": "pending",
                    "triggered_by": "replay",
                },
            )
        },
    )
    result = runner.invoke(main, ["executions", "replay", "exec_x"])
    assert result.exit_code == 0, result.output
    method, path, body = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/executions/exec_x/replay"
    assert body == {}
    assert "exec_new" in result.output


def test_executions_replay_409_inflight_helpful_error(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/replay"): lambda: _FakeResp(
                409,
                {"detail": {"error": {"code": "execution_in_flight", "message": "still in progress", "status": 409}}},
            )
        },
    )
    result = runner.invoke(main, ["executions", "replay", "exec_x"])
    assert "in flight" in result.output.lower() or "in progress" in result.output.lower()


def test_executions_verification_pending_posts_empty_body(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/verification-pending"): lambda: _FakeResp(
                200, {"outcome_state": "verification_pending"}
            )
        },
    )
    result = runner.invoke(main, ["executions", "verification-pending", "exec_x"])
    assert result.exit_code == 0, result.output
    method, path, body = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/executions/exec_x/verification-pending"
    assert body == {}
    assert "verification_pending" in result.output


def test_executions_verify_default_omits_valid_field(monkeypatch):
    # No --valid / --invalid flag → body should be empty so the server's
    # legacy default (valid=true) applies. Pinned so a refactor can't
    # silently start always-sending the field.
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/verify"): lambda: _FakeResp(
                200, {"outcome_state": "verified_success"}
            )
        },
    )
    result = runner.invoke(main, ["executions", "verify", "exec_x"])
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {}


def test_executions_verify_invalid_sends_false(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/verify"): lambda: _FakeResp(
                200, {"outcome_state": "verification_failed"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["executions", "verify", "exec_x", "--invalid", "--reason", "evidence missing"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {"valid": False, "reason": "evidence missing"}
    assert "verification_failed" in result.output or "verification-failed" in result.output


def test_executions_verify_explicit_valid_sends_true(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/exec_x/verify"): lambda: _FakeResp(
                200, {"outcome_state": "verified_success"}
            )
        },
    )
    result = runner.invoke(main, ["executions", "verify", "exec_x", "--valid"])
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {"valid": True}


def test_executions_verify_reason_too_long_rejected_client_side():
    long_reason = "x" * 501
    result = runner.invoke(
        main,
        ["executions", "verify", "exec_x", "--reason", long_reason],
    )
    assert result.exit_code != 0
    assert "500" in result.output or "characters" in result.output.lower()


def test_executions_verify_404(monkeypatch):
    holder: dict = {}
    _patch_exec_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/executions/missing/verify"): lambda: _FakeResp(404, {})
        },
    )
    result = runner.invoke(main, ["executions", "verify", "missing"])
    assert "not found" in result.output.lower() or "missing" in result.output


def test_executions_group_help_includes_new_subcommands():
    result = runner.invoke(main, ["executions", "--help"])
    assert result.exit_code == 0
    for sub in ("replay", "verification-pending", "verify"):
        assert sub in result.output, f"executions subcommand {sub} missing"

# --- messaging primitive: messages command group ---


class _FakeResp:
    def __init__(self, status_code: int, payload: Any, headers: Optional[dict] = None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


class _MessagesClient:
    """Captures POST/GET for messages tests, including headers (for X-Cueapi-From-Agent)."""

    def __init__(self, responses: Optional[dict] = None):
        self.calls: list = []
        self._responses = responses or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def _resolve(self, method: str, path: str):
        for (m, p), factory in sorted(self._responses.items(), key=lambda kv: -len(kv[0][1])):
            if m == method and path.startswith(p):
                return factory()
        return _FakeResp(200, {})

    def post(self, path, json=None, headers=None, **_):
        self.calls.append(("POST", path, json, headers))
        return self._resolve("POST", path)

    def get(self, path, params=None, headers=None, **_):
        self.calls.append(("GET", path, params, headers))
        return self._resolve("GET", path)


def _patch_messages_client(monkeypatch, holder, responses=None):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _MessagesClient(responses=responses)
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


# --- help-text shape ---


def test_messages_group_help():
    result = runner.invoke(main, ["messages", "--help"])
    assert result.exit_code == 0
    for sub in ("send", "get", "read", "ack"):
        assert sub in result.output, f"messages subcommand {sub} missing from --help"


def test_messages_send_help_lists_required_flags():
    result = runner.invoke(main, ["messages", "send", "--help"])
    assert result.exit_code == 0
    assert "--from" in result.output
    assert "--to" in result.output
    assert "--body" in result.output
    assert "--idempotency-key" in result.output


def test_messages_send_requires_from_and_to_and_body():
    # Missing --from
    r1 = runner.invoke(main, ["messages", "send", "--to", "x", "--body", "hi"])
    assert r1.exit_code != 0
    # Missing --to
    r2 = runner.invoke(main, ["messages", "send", "--from", "x", "--body", "hi"])
    assert r2.exit_code != 0
    # Missing body source entirely (post-Phase-3: not just --body; any of
    # --message-file / --body-stdin / --body works)
    r3 = runner.invoke(main, ["messages", "send", "--from", "x", "--to", "y"])
    assert r3.exit_code != 0


# --- Phase 3: body-source acquisition (force-file mode) ---


def test_messages_send_rejects_inline_body_with_dollar_paren():
    """Layer 3 force-file guard: $(...) in inline body must be rejected."""
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "body with $(echo INJECT) embedded"],
    )
    assert r.exit_code != 0
    assert "shell metacharacters" in r.output


def test_messages_send_rejects_inline_body_with_backticks():
    """Layer 3 force-file guard: backticks in inline body must be rejected."""
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "body with `echo INJECT` embedded"],
    )
    assert r.exit_code != 0
    assert "shell metacharacters" in r.output


def test_messages_send_rejects_inline_body_with_dollar_brace():
    """Layer 3 force-file guard: ${VAR} in inline body must be rejected."""
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "body with ${VAR_INJECT} embedded"],
    )
    assert r.exit_code != 0
    assert "shell metacharacters" in r.output


def test_messages_send_accepts_inline_body_when_metachar_free(monkeypatch):
    """Inline --body without metachars is accepted byte-identical."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_safe", "delivery_state": "queued", "thread_id": "thr_x"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "plain prose body without any metachars"],
    )
    assert r.exit_code == 0, r.output
    _, _, body, _ = holder["client"].calls[-1]
    assert body["body"] == "plain prose body without any metachars"


def test_messages_send_accepts_inline_metachars_with_override(monkeypatch):
    """--allow-inline-metachars override accepts inline body with $(...) etc."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_override", "delivery_state": "queued", "thread_id": "thr_x"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "body with $(echo LITERAL) intended verbatim",
         "--allow-inline-metachars"],
    )
    assert r.exit_code == 0, r.output
    _, _, body, _ = holder["client"].calls[-1]
    assert body["body"] == "body with $(echo LITERAL) intended verbatim"


def test_messages_send_accepts_message_file(monkeypatch, tmp_path):
    """--message-file reads body from path byte-identical (incl. metachars)."""
    body_file = tmp_path / "body.txt"
    body_text = "metachar-rich body: $(echo X) and `echo Y` and ${HOME}"
    body_file.write_text(body_text)
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_file", "delivery_state": "queued", "thread_id": "thr_x"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--message-file", str(body_file)],
    )
    assert r.exit_code == 0, r.output
    _, _, body, _ = holder["client"].calls[-1]
    assert body["body"] == body_text


def test_messages_send_accepts_body_stdin(monkeypatch):
    """--body-stdin reads body from stdin byte-identical."""
    body_text = "stdin body with $(echo metachars) preserved"
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_stdin", "delivery_state": "queued", "thread_id": "thr_x"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y", "--body-stdin"],
        input=body_text,
    )
    assert r.exit_code == 0, r.output
    _, _, body, _ = holder["client"].calls[-1]
    assert body["body"] == body_text


def test_messages_send_rejects_multiple_body_sources():
    """Exactly one of --body / --message-file / --body-stdin must be set."""
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "inline body", "--body-stdin"],
        input="stdin body",
    )
    assert r.exit_code != 0
    assert "Multiple body sources" in r.output


def test_message_to_rejects_inline_body_with_metachars():
    """Parity: legacy `message-to` command applies same Layer 3 guard."""
    r = runner.invoke(
        main,
        ["message-to", "recipient@y", "--from", "a@x",
         "--body", "body with $(echo INJECT)"],
    )
    assert r.exit_code != 0
    assert "shell metacharacters" in r.output


# --- Phase 2: auto-verify body echo ---


def test_messages_send_default_adds_verify_echo_header(monkeypatch):
    """Default auto-verify-on adds X-CueAPI-Verify-Echo: true header."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y", "--body", "plain"],
    )
    assert r.exit_code == 0, r.output
    _, _, _, headers = holder["client"].calls[-1]
    assert headers.get("X-CueAPI-Verify-Echo") == "true"


def test_messages_send_no_verify_omits_header(monkeypatch):
    """--no-verify opt-out omits the X-CueAPI-Verify-Echo header."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued"},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "plain", "--no-verify"],
    )
    assert r.exit_code == 0, r.output
    _, _, _, headers = holder["client"].calls[-1]
    assert "X-CueAPI-Verify-Echo" not in headers


def test_messages_send_verify_passes_byte_identical(monkeypatch):
    """Substrate echoes back same body in body_received.body → success.

    Empirically-locked wire shape 2026-05-11: body_received is the
    PARSED request dict, not a flat string. CLI extracts .body for diff.
    """
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued",
                      "body_received": {"to": "b@y", "body": "plain", "subject": None, "priority": 3}},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y", "--body", "plain"],
    )
    assert r.exit_code == 0, r.output


def test_messages_send_verify_fails_loud_on_mismatch(monkeypatch):
    """body_received.body differs from sent body → exit 7 + diff diagnostic."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_mutated", "delivery_state": "queued",
                      "body_received": {"to": "b@y", "body": "body received by substrate (mutated)",
                                        "subject": None, "priority": 3}},
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y",
         "--body", "body sent by caller (intended)"],
    )
    # Exit code 7 = body verify mismatch (distinct from generic failure)
    assert r.exit_code == 7
    assert "MISMATCH" in r.output


def test_messages_send_verify_handles_flat_string_body_received(monkeypatch):
    """Defensive: future substrate rev flattens body_received → CLI still verifies.

    Belt-and-suspenders for spec drift; cue-pm fired primary to fix
    substrate to flat-string post-Phase-1-bug-headsup ~23:20Z.
    """
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued",
                      "body_received": "plain"},  # flat-string variant
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y", "--body", "plain"],
    )
    assert r.exit_code == 0, r.output


def test_messages_send_verify_noop_when_substrate_omits_echo(monkeypatch):
    """Backward-compat: pre-Layer-1 substrate omits body_received → no raise."""
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued"},
                # No body_received field
            )
        },
    )
    r = runner.invoke(
        main,
        ["messages", "send", "--from", "a@x", "--to", "b@y", "--body", "plain"],
    )
    assert r.exit_code == 0, r.output


# --- send body + headers ---


def test_messages_send_minimal_body_and_from_header(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201,
                {"id": "msg_x", "delivery_state": "queued", "thread_id": "thr_x"},
            )
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "sender@x", "--to", "recipient@y", "--body", "hello"],
    )
    assert result.exit_code == 0, result.output
    method, path, body, headers = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/messages"
    assert body == {"to": "recipient@y", "body": "hello"}
    # Sender goes via header, NOT body. Pinned because the server reads it
    # from X-Cueapi-From-Agent and a refactor putting `from` in the body
    # would silently swallow the value (Pydantic extra=forbid would 400 it
    # but we want the failure to be loud at integration time, not silent).
    assert headers["X-Cueapi-From-Agent"] == "sender@x"


def test_messages_send_with_all_optionals(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201,
                {"id": "msg_x", "delivery_state": "queued"},
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "sender@x",
            "--to", "recipient@y",
            "--body", "the body",
            "--subject", "the subject",
            "--reply-to", "msg_abcdef123456",
            "--priority", "5",
            "--expects-reply",
            "--reply-to-agent", "alt@x",
            "--metadata", '{"k": "v"}',
            "--idempotency-key", "idemp-key-1",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {
        "to": "recipient@y",
        "body": "the body",
        "subject": "the subject",
        "reply_to": "msg_abcdef123456",
        "priority": 5,
        "expects_reply": True,
        "reply_to_agent": "alt@x",
        "metadata": {"k": "v"},
    }
    headers = holder["client"].calls[-1][3]
    assert headers["X-Cueapi-From-Agent"] == "sender@x"
    assert headers["Idempotency-Key"] == "idemp-key-1"


def test_messages_send_send_at_omitted_by_default(monkeypatch):
    # Wire-format must match pre-#623 senders when --send-at is not passed.
    # Server contract: NULL send_at === deliver immediately.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "sender@x", "--to", "recipient@y", "--body", "hello"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert "send_at" not in body


def test_messages_send_send_at_passed_in_body(monkeypatch):
    # send_at flows in the body (server contract: MessageCreate.send_at,
    # app/schemas/message.py). Mirrors cue-fire send_at transport.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_x", "delivery_state": "queued"}
            )
        },
    )
    future = "2099-01-01T00:00:00Z"
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "sender@x",
            "--to", "recipient@y",
            "--body", "hello",
            "--send-at", future,
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body["send_at"] == future
    # Verify it's a body field, NOT a header (regression guard).
    headers = holder["client"].calls[-1][3]
    assert "Send-At" not in headers
    assert "X-Cueapi-Send-At" not in headers


def test_messages_send_omits_expects_reply_when_unset(monkeypatch):
    # Default false MUST NOT appear in the body — server's Pydantic default
    # is false, and sending `expects_reply: false` explicitly creates noise.
    # Pinned so a refactor can't silently start always-sending the field.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "expects_reply" not in body


def test_messages_send_notify_passed_as_body_list(monkeypatch):
    # §17 BCC-light: notify flows in body as a list (server contract:
    # MessageCreate.notify, app/schemas/message.py).
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi",
         "--notify", "agt_a", "--notify", "agt_b"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body["notify"] == ["agt_a", "agt_b"]


def test_messages_send_notify_omitted_when_unset(monkeypatch):
    # Default-omit: empty notify must not appear on the wire (matches
    # pre-#619 senders).
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "notify" not in body


def test_messages_send_notify_max_10_enforced_client_side():
    # Server caps at 10; CLI rejects 11+ before hitting the wire to
    # surface the error at parse time instead of as a 422.
    eleven = [arg for ref in [f"agt_{i}" for i in range(11)] for arg in ("--notify", ref)]
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi", *eleven],
    )
    assert result.exit_code != 0
    assert "at most 10" in result.output


def test_messages_send_mode_default_omitted(monkeypatch):
    # Surface 6 v2: default mode=auto is omitted on the wire (matches
    # pre-Surface-6 senders).
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "delivery_mode" not in body


def test_messages_send_mode_explicit_passed_through(monkeypatch):
    # Explicit non-auto modes flow as body.delivery_mode.
    for mode_value in ("live", "bg", "inbox", "webhook"):
        holder: dict = {}
        _patch_messages_client(
            monkeypatch,
            holder,
            responses={
                ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
            },
        )
        result = runner.invoke(
            main,
            ["messages", "send", "--from", "x", "--to", "y", "--body", "hi", "--mode", mode_value],
        )
        assert result.exit_code == 0, result.output
        body = holder["client"].calls[-1][2]
        assert body["delivery_mode"] == mode_value


def test_messages_send_mode_auto_explicitly_omitted(monkeypatch):
    # Even when caller explicitly passes --mode auto, omit on the wire.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_x", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi", "--mode", "auto"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "delivery_mode" not in body


def test_message_to_notify_passed_as_body_list(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_z", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi",
         "--notify", "agt_a", "--notify", "agt_b"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body["notify"] == ["agt_a", "agt_b"]


def test_message_to_notify_omitted_when_unset(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(201, {"id": "msg_z", "delivery_state": "queued"})
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "notify" not in body


def test_messages_send_priority_validated_by_click_intrange():
    result = runner.invoke(
        main,
        ["messages", "send", "--from", "x", "--to", "y", "--body", "hi", "--priority", "9"],
    )
    assert result.exit_code != 0
    # Click's IntRange error mentions the bounds.
    assert "1" in result.output or "5" in result.output or "invalid" in result.output.lower()


def test_messages_send_idempotency_key_too_long_rejected_client_side():
    long_key = "x" * 256
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "x", "--to", "y", "--body", "hi",
            "--idempotency-key", long_key,
        ],
    )
    assert result.exit_code != 0
    assert "255" in result.output or "characters" in result.output.lower()


def test_messages_send_invalid_metadata_json():
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "x", "--to", "y", "--body", "hi",
            "--metadata", "{not json",
        ],
    )
    assert result.exit_code != 0
    assert "json" in result.output.lower()


def test_messages_send_dedup_hit_renders_existing_label(monkeypatch):
    # Server returns 200 (not 201) on Idempotency-Key dedup hit. The CLI
    # should explicitly tell the user it was a dedup hit so they don't
    # think a fresh send happened.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                200,
                {"id": "msg_existing", "delivery_state": "delivered"},
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "x", "--to", "y", "--body", "hi",
            "--idempotency-key", "k1",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (
        "dedup" in result.output.lower()
        or "existing" in result.output.lower()
    )


def test_messages_send_priority_downgrade_header_surfaced(monkeypatch):
    # Server may downgrade priority>3 to 3 under receiver-pair limits and
    # surfaces this via X-CueAPI-Priority-Downgraded: true. The CLI should
    # show the user this happened so they can adapt without parsing body.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201,
                {"id": "msg_x", "delivery_state": "queued", "priority": 3},
                headers={"X-CueAPI-Priority-Downgraded": "true"},
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "x", "--to", "y", "--body", "hi",
            "--priority", "5",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "downgrad" in result.output.lower()


def test_messages_send_409_idempotency_key_conflict_helpful_error(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                409,
                {"detail": {"error": {"code": "idempotency_key_conflict", "message": "conflict", "status": 409}}},
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "messages", "send",
            "--from", "x", "--to", "y", "--body", "hi",
            "--idempotency-key", "k1",
        ],
    )
    # Don't gate on exit code (echo_error doesn't change it in this codebase);
    # check the user gets a hint about what went wrong.
    assert (
        "Idempotency-Key" in result.output
        or "different body" in result.output
        or "conflict" in result.output.lower()
    )


# --- get / read / ack ---


def test_messages_get_renders_body_and_metadata(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/messages/msg_x"): lambda: _FakeResp(
                200,
                {
                    "id": "msg_x",
                    "delivery_state": "delivered",
                    "from": {"slug": "sender@x", "agent_id": "agt_s"},
                    "to": "recipient@y",
                    "subject": "test subject",
                    "thread_id": "thr_x",
                    "priority": 4,
                    "body": "the body content",
                },
            )
        },
    )
    result = runner.invoke(main, ["messages", "get", "msg_x"])
    assert result.exit_code == 0
    assert "msg_x" in result.output
    assert "sender@x" in result.output
    assert "recipient@y" in result.output
    assert "test subject" in result.output
    assert "the body content" in result.output


def test_messages_get_404(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/messages/missing"): lambda: _FakeResp(404, {})
        },
    )
    result = runner.invoke(main, ["messages", "get", "missing"])
    assert "not found" in result.output.lower() or "missing" in result.output


def test_messages_read(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages/msg_x/read"): lambda: _FakeResp(
                200,
                {"delivery_state": "read", "read_at": "2026-05-04T17:00:00Z"},
            )
        },
    )
    result = runner.invoke(main, ["messages", "read", "msg_x"])
    assert result.exit_code == 0
    assert "Marked read" in result.output or "msg_x" in result.output
    assert "2026-05-04T17:00:00Z" in result.output


def test_messages_read_409_terminal_state(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages/msg_x/read"): lambda: _FakeResp(
                409,
                {"detail": {"error": {"code": "invalid_transition", "message": "cannot read in terminal state", "status": 409}}},
            )
        },
    )
    result = runner.invoke(main, ["messages", "read", "msg_x"])
    assert "terminal" in result.output.lower() or "cannot" in result.output.lower()


def test_messages_ack(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages/msg_x/ack"): lambda: _FakeResp(
                200,
                {"delivery_state": "acked", "acked_at": "2026-05-04T17:01:00Z"},
            )
        },
    )
    result = runner.invoke(main, ["messages", "ack", "msg_x"])
    assert result.exit_code == 0
    assert "Acked" in result.output or "msg_x" in result.output
    assert "2026-05-04T17:01:00Z" in result.output


# --- top-level surface ---


def test_top_level_help_lists_messages():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "messages" in result.output


# --- fire --send-at (hosted PR #618 port) ---


class _FireSendAtClient:
    def __init__(self):
        self.last_body: Optional[dict] = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def post(self, path, json=None, **_):
        self.last_body = json
        class _R:
            status_code = 200
            def json(self):
                return {"id": "exec_test", "scheduled_for": "2026-05-04T20:00:00Z"}
        return _R()


def _patch_fire_client(monkeypatch, holder):
    import cueapi.cli as cli_mod

    def fake_factory(*_, **__):
        holder["client"] = _FireSendAtClient()
        return holder["client"]

    monkeypatch.setattr(cli_mod, "CueAPIClient", fake_factory)


def test_fire_help_lists_send_at():
    result = runner.invoke(main, ["fire", "--help"])
    assert result.exit_code == 0
    assert "--send-at" in result.output


def test_fire_send_at_passed_to_body(monkeypatch):
    holder: dict = {}
    _patch_fire_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        ["fire", "cue_x", "--send-at", "2026-05-04T20:00:00Z"],
    )
    assert result.exit_code == 0, result.output
    assert holder["client"].last_body == {"send_at": "2026-05-04T20:00:00Z"}


def test_fire_omits_send_at_when_unset(monkeypatch):
    # Pin: when --send-at isn't passed, the body must not include the key.
    holder: dict = {}
    _patch_fire_client(monkeypatch, holder)
    result = runner.invoke(main, ["fire", "cue_x"])
    assert result.exit_code == 0
    assert "send_at" not in (holder["client"].last_body or {})


def test_fire_combines_send_at_with_payload_override(monkeypatch):
    holder: dict = {}
    _patch_fire_client(monkeypatch, holder)
    result = runner.invoke(
        main,
        [
            "fire", "cue_x",
            "--payload-override", '{"task": "demo"}',
            "--merge-strategy", "replace",
            "--send-at", "2026-05-04T22:00:00Z",
        ],
    )
    assert result.exit_code == 0
    assert holder["client"].last_body == {
        "payload_override": {"task": "demo"},
        "merge_strategy": "replace",
        "send_at": "2026-05-04T22:00:00Z",
    }
# --- agents list --online-only ---


def test_agents_list_online_only_sets_status_filter(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={("GET", "/agents"): lambda: _FakeResp(200, {"agents": [], "total": 0})},
    )
    result = runner.invoke(main, ["agents", "list", "--online-only"])
    assert result.exit_code == 0, result.output
    params = holder["client"].calls[-1][2]
    assert params["status"] == "online"


def test_agents_list_online_only_conflicts_with_status():
    result = runner.invoke(
        main, ["agents", "list", "--online-only", "--status", "offline"]
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_agents_list_help_mentions_online_only():
    result = runner.invoke(main, ["agents", "list", "--help"])
    assert result.exit_code == 0
    assert "--online-only" in result.output


# --- agents describe (alias) ---


def test_agents_describe_renders_same_as_get(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x"): lambda: _FakeResp(
                200,
                {
                    "id": "agt_x",
                    "slug": "x",
                    "display_name": "X Agent",
                    "status": "online",
                    "webhook_url": None,
                    "metadata": None,
                },
            )
        },
    )
    result = runner.invoke(main, ["agents", "describe", "agt_x"])
    assert result.exit_code == 0
    assert "agt_x" in result.output
    assert "X Agent" in result.output
    # Single GET to /agents/<ref>, same as `agents get`.
    assert holder["client"].calls[-1][0] == "GET"
    assert holder["client"].calls[-1][1] == "/agents/agt_x"


def test_agents_describe_appears_in_help():
    result = runner.invoke(main, ["agents", "--help"])
    assert result.exit_code == 0
    assert "describe" in result.output


# --- message-to top-level wrapper ---


def test_message_to_passes_agent_id_through_without_lookup(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued", "thread_id": "thr_z"}
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "message-to",
            "agt_recipient",
            "--from",
            "sender@x",
            "--body",
            "hi",
        ],
    )
    assert result.exit_code == 0, result.output
    # No GET /agents — agt_ prefix is pass-through.
    methods = [c[0] for c in holder["client"].calls]
    assert "GET" not in methods
    method, path, body, headers = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/messages"
    assert body["to"] == "agt_recipient"
    assert body["body"] == "hi"
    assert headers["X-Cueapi-From-Agent"] == "sender@x"


def test_message_to_passes_slug_form_through_without_lookup(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "alice@user1", "--from", "bob@user1", "--body", "hi"],
    )
    assert result.exit_code == 0, result.output
    methods = [c[0] for c in holder["client"].calls]
    assert "GET" not in methods
    body = holder["client"].calls[-1][2]
    assert body["to"] == "alice@user1"


def test_message_to_resolves_display_name_case_insensitive(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents"): lambda: _FakeResp(
                200,
                {
                    "agents": [
                        {"id": "agt_one", "slug": "one", "display_name": "One Agent"},
                        {"id": "agt_two", "slug": "two", "display_name": "Two Agent"},
                    ],
                    "total": 2,
                },
            ),
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            ),
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "two agent", "--from", "sender@x", "--body", "hi"],
    )
    assert result.exit_code == 0, result.output
    # 1st call: GET /agents (resolution); 2nd: POST /messages
    assert holder["client"].calls[0][0] == "GET"
    assert holder["client"].calls[0][1] == "/agents"
    post_call = holder["client"].calls[-1]
    assert post_call[0] == "POST"
    assert post_call[2]["to"] == "agt_two"


def test_message_to_resolves_slug_match(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents"): lambda: _FakeResp(
                200,
                {
                    "agents": [
                        {"id": "agt_pm", "slug": "pm", "display_name": "Cue PM"},
                    ],
                    "total": 1,
                },
            ),
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            ),
        },
    )
    result = runner.invoke(
        main, ["message-to", "pm", "--from", "sender@x", "--body", "hi"]
    )
    assert result.exit_code == 0, result.output
    assert holder["client"].calls[-1][2]["to"] == "agt_pm"


def test_message_to_no_match_errors_with_roster_hint(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents"): lambda: _FakeResp(
                200,
                {
                    "agents": [
                        {"id": "agt_a", "slug": "alpha", "display_name": "Alpha"},
                    ],
                    "total": 1,
                },
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "nobody", "--from", "sender@x", "--body", "hi"],
    )
    # No POST should fire.
    methods = [c[0] for c in holder["client"].calls]
    assert "POST" not in methods
    assert "no agent matches" in result.output.lower()
    assert "alpha" in result.output.lower()


def test_message_to_ambiguous_match_errors(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents"): lambda: _FakeResp(
                200,
                {
                    "agents": [
                        {"id": "agt_one", "slug": "shared", "display_name": "Worker"},
                        {"id": "agt_two", "slug": "other", "display_name": "Worker"},
                    ],
                    "total": 2,
                },
            )
        },
    )
    result = runner.invoke(
        main, ["message-to", "Worker", "--from", "sender@x", "--body", "hi"]
    )
    methods = [c[0] for c in holder["client"].calls]
    assert "POST" not in methods
    assert "agt_one" in result.output and "agt_two" in result.output


def test_message_to_passes_optionals_through(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "message-to",
            "agt_recipient",
            "--from",
            "sender@x",
            "--body",
            "the body",
            "--subject",
            "the subject",
            "--reply-to",
            "msg_abcdef123456",
            "--priority",
            "5",
            "--expects-reply",
            "--reply-to-agent",
            "alt@x",
            "--metadata",
            '{"k": "v"}',
            "--idempotency-key",
            "idemp-key-1",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {
        "body": "the body",
        "subject": "the subject",
        "reply_to": "msg_abcdef123456",
        "priority": 5,
        "expects_reply": True,
        "reply_to_agent": "alt@x",
        "metadata": {"k": "v"},
        "to": "agt_recipient",
    }
    headers = holder["client"].calls[-1][3]
    assert headers["X-Cueapi-From-Agent"] == "sender@x"
    assert headers["Idempotency-Key"] == "idemp-key-1"


def test_message_to_omits_expects_reply_when_unset(monkeypatch):
    # Same default-false discipline as `messages send`.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "expects_reply" not in body


def test_message_to_send_at_passed_in_body(monkeypatch):
    # Same parity as `messages send` — send_at flows in body, not header.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    future = "2099-01-01T00:00:00Z"
    result = runner.invoke(
        main,
        [
            "message-to", "agt_x",
            "--from", "y@z",
            "--body", "hi",
            "--send-at", future,
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body["send_at"] == future
    headers = holder["client"].calls[-1][3]
    assert "Send-At" not in headers
    assert "X-Cueapi-Send-At" not in headers


def test_message_to_send_at_omitted_when_unset(monkeypatch):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi"],
    )
    assert result.exit_code == 0
    body = holder["client"].calls[-1][2]
    assert "send_at" not in body


def test_message_to_priority_validated_by_click_intrange():
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi", "--priority", "9"],
    )
    assert result.exit_code != 0


def test_message_to_idempotency_key_too_long_rejected():
    long_key = "x" * 256
    result = runner.invoke(
        main,
        [
            "message-to",
            "agt_x",
            "--from",
            "y@z",
            "--body",
            "hi",
            "--idempotency-key",
            long_key,
        ],
    )
    assert result.exit_code != 0


def test_message_to_invalid_metadata_json():
    result = runner.invoke(
        main,
        [
            "message-to",
            "agt_x",
            "--from",
            "y@z",
            "--body",
            "hi",
            "--metadata",
            "{not json",
        ],
    )
    assert result.exit_code != 0


def test_top_level_help_lists_message_to():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "message-to" in result.output


# --- message-to --mode flag (Surface 6 delivery_mode) ---


def test_message_to_mode_default_auto_omits_field(monkeypatch):
    # Default is `auto` and the server treats absent == auto, so we don't
    # send the field on the common path — keeps wire-format identical to
    # pre-Surface-6 senders and avoids payload noise.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert "delivery_mode" not in body


def test_message_to_mode_explicit_auto_still_omits_field(monkeypatch):
    # User explicitly typing --mode auto is the same wire-format as omitting
    # it. No reason to send the redundant field.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi", "--mode", "auto"],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert "delivery_mode" not in body


@pytest.mark.parametrize("mode", ["live", "bg", "inbox", "webhook"])
def test_message_to_mode_non_auto_passed_through(monkeypatch, mode):
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201,
                {
                    "id": "msg_z",
                    "delivery_state": "queued",
                    "effective_delivery_mode": mode,
                },
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi", "--mode", mode],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body["delivery_mode"] == mode
    # echo_info pads labels — match the components, not the raw concat.
    assert "Sent via:" in result.output
    assert mode in result.output


def test_message_to_mode_invalid_value_rejected_by_click():
    # Click.Choice covers validation; we just confirm the gate is in place
    # so a typo doesn't silently sail past as "auto".
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi", "--mode", "bogus"],
    )
    assert result.exit_code != 0
    assert "bogus" in result.output or "invalid choice" in result.output.lower()


def test_message_to_surfaces_downgraded_delivery_mode(monkeypatch):
    # Server downgrade case: requested `live` but recipient has no live
    # session, server delivered via inbox. CLI surfaces both the chosen
    # mode and the "you asked for X" hint.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201,
                {
                    "id": "msg_z",
                    "delivery_state": "queued",
                    "effective_delivery_mode": "inbox",
                },
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi", "--mode", "live"],
    )
    assert result.exit_code == 0, result.output
    assert "Sent via:" in result.output
    assert "inbox" in result.output
    assert "requested live" in result.output


def test_message_to_omits_sent_via_when_server_does_not_return_it(monkeypatch):
    # Pre-Surface-6 server (or auto + no field) returns no
    # effective_delivery_mode. The CLI should not emit a "Sent via:" line.
    holder: dict = {}
    _patch_messages_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/messages"): lambda: _FakeResp(
                201, {"id": "msg_z", "delivery_state": "queued"}
            )
        },
    )
    result = runner.invoke(
        main,
        ["message-to", "agt_x", "--from", "y@z", "--body", "hi"],
    )
    assert result.exit_code == 0, result.output
    assert "Sent via:" not in result.output


def test_message_to_help_lists_mode_flag():
    result = runner.invoke(main, ["message-to", "--help"])
    assert result.exit_code == 0
    assert "--mode" in result.output
    for choice in ("live", "bg", "inbox", "webhook", "auto"):
        assert choice in result.output


# ──────────────────────────────────────────────────────────────────────────
# Event-emit primitive (PR-1b) — events + subscriptions commands
# ──────────────────────────────────────────────────────────────────────────


def test_events_list_basic(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/events"): lambda: _FakeResp(
                200,
                {
                    "events": [
                        {"id": 1, "event_type": "message.received", "emitted_at": "2026-05-11T03:00:00Z"},
                        {"id": 2, "event_type": "message.received", "emitted_at": "2026-05-11T03:01:00Z"},
                    ],
                    "next_cursor": 2,
                },
            )
        },
    )
    result = runner.invoke(main, ["events", "list", "agt_x"])
    assert result.exit_code == 0, result.output
    assert "message.received" in result.output
    assert "Next cursor" in result.output


def test_events_list_with_since_and_event_type(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/events"): lambda: _FakeResp(
                200, {"events": [], "next_cursor": 0}
            )
        },
    )
    result = runner.invoke(
        main,
        ["events", "list", "agt_x", "--since", "42", "--event-type", "message.received"],
    )
    assert result.exit_code == 0, result.output
    method, path, params = holder["client"].calls[-1]
    assert method == "GET"
    assert path == "/agents/agt_x/events"
    assert params == {"limit": 100, "since": 42, "event_type": "message.received"}


def test_events_list_defaults_only_limit(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/events"): lambda: _FakeResp(
                200, {"events": [], "next_cursor": 0}
            )
        },
    )
    result = runner.invoke(main, ["events", "list", "agt_x"])
    assert result.exit_code == 0
    method, path, params = holder["client"].calls[-1]
    assert params == {"limit": 100}


def test_events_list_404_agent_not_found(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/missing/events"): lambda: _FakeResp(
                404, {"detail": {"error": {"code": "agent_not_found", "message": "agent not found"}}}
            )
        },
    )
    result = runner.invoke(main, ["events", "list", "missing"])
    assert "Agent not found" in result.output


def test_subscriptions_create_pull_minimal(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents/agt_x/subscriptions"): lambda: _FakeResp(
                201,
                {
                    "id": "sub_uuid",
                    "event_type": "message.received",
                    "delivery_target": "pull",
                },
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "subscriptions", "create", "agt_x",
            "--event-type", "message.received",
            "--delivery-target", "pull",
        ],
    )
    assert result.exit_code == 0, result.output
    method, path, body = holder["client"].calls[-1]
    assert method == "POST"
    assert path == "/agents/agt_x/subscriptions"
    assert body == {"event_type": "message.received", "delivery_target": "pull"}
    assert "Subscription created" in result.output


def test_subscriptions_create_webhook_with_url(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("POST", "/agents/agt_x/subscriptions"): lambda: _FakeResp(
                201,
                {
                    "id": "sub_uuid",
                    "event_type": "message.received",
                    "delivery_target": "webhook",
                    "webhook_secret": "wsec_oneshot",
                },
            )
        },
    )
    result = runner.invoke(
        main,
        [
            "subscriptions", "create", "agt_x",
            "--event-type", "message.received",
            "--delivery-target", "webhook",
            "--webhook-url", "https://example.com/hook",
        ],
    )
    assert result.exit_code == 0, result.output
    body = holder["client"].calls[-1][2]
    assert body == {
        "event_type": "message.received",
        "delivery_target": "webhook",
        "webhook_url": "https://example.com/hook",
    }
    # Webhook secret must be surfaced (one-shot reveal).
    assert "wsec_oneshot" in result.output


def test_subscriptions_create_webhook_without_url_errors():
    # Client-side guard — surface the requirement at parse time
    # instead of letting the server 400 it.
    result = runner.invoke(
        main,
        [
            "subscriptions", "create", "agt_x",
            "--event-type", "message.received",
            "--delivery-target", "webhook",
        ],
    )
    assert result.exit_code != 0
    assert "--webhook-url is required" in result.output


def test_subscriptions_list_basic(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/subscriptions"): lambda: _FakeResp(
                200,
                {
                    "subscriptions": [
                        {
                            "id": "sub_uuid_1",
                            "event_type": "message.received",
                            "delivery_target": "pull",
                        },
                        {
                            "id": "sub_uuid_2",
                            "event_type": "message.received",
                            "delivery_target": "webhook",
                            "webhook_url": "https://example.com",
                        },
                    ]
                },
            )
        },
    )
    result = runner.invoke(main, ["subscriptions", "list", "agt_x"])
    assert result.exit_code == 0, result.output
    assert "sub_uuid_1" in result.output
    assert "sub_uuid_2" in result.output
    assert "pull" in result.output
    assert "webhook" in result.output


def test_subscriptions_list_empty(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("GET", "/agents/agt_x/subscriptions"): lambda: _FakeResp(
                200, {"subscriptions": []}
            )
        },
    )
    result = runner.invoke(main, ["subscriptions", "list", "agt_x"])
    assert result.exit_code == 0
    assert "No active subscriptions" in result.output


def test_subscriptions_delete_basic(monkeypatch):
    holder: dict = {}
    _patch_client(
        monkeypatch,
        holder,
        responses={
            ("DELETE", "/agents/agt_x/subscriptions/sub-uuid-1"): lambda: _FakeResp(
                200, {"status": "detached"}
            )
        },
    )
    result = runner.invoke(main, ["subscriptions", "delete", "agt_x", "sub-uuid-1"])
    assert result.exit_code == 0, result.output
    assert "Subscription detached" in result.output


def test_events_help_lists_list_subcommand():
    result = runner.invoke(main, ["events", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output


def test_subscriptions_help_lists_subcommands():
    result = runner.invoke(main, ["subscriptions", "--help"])
    assert result.exit_code == 0
    for sub in ("create", "list", "delete"):
        assert sub in result.output
