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
