"""Unit tests for cueapi CLI commands using Click's CliRunner.

No live API calls — tests only verify CLI entry points, help text, and argument parsing.
"""

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
