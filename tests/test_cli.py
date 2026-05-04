"""Unit tests for cueapi CLI commands using Click's CliRunner.

No live API calls — tests only verify CLI entry points, help text, and argument parsing.
"""

from typing import Any, Optional

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
