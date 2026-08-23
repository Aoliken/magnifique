"""Integration coverage for the Compose migration startup gate."""

from __future__ import annotations

import subprocess
import os
from pathlib import Path

import pytest

from scripts.start_stack import ServiceVerificationError, run_startup


class _CompletedProcess:
    def __init__(self, args: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_startup_verifies_service_then_runs_migration_then_starts_stack():
    recorded_commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        recorded_commands.append(command)
        if command == ["docker", "compose", "config", "--services"]:
            return _CompletedProcess(command, stdout="postgres\nflask-app\nauth-service\ngame-service\n")
        if command == ["docker", "compose", "run", "--rm", "flask-app", "alembic", "upgrade", "head"]:
            return _CompletedProcess(command)
        if command == ["docker", "compose", "up", "--detach"]:
            return _CompletedProcess(command)
        raise AssertionError(f"Unexpected command: {command}")

    exit_code = run_startup(["--detach"], run_command=fake_run)

    assert exit_code == 0
    assert recorded_commands == [
        ["docker", "compose", "config", "--services"],
        ["docker", "compose", "run", "--rm", "flask-app", "alembic", "upgrade", "head"],
        ["docker", "compose", "up", "--detach"],
    ]


def test_run_startup_fails_fast_when_migration_command_fails():
    recorded_commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        recorded_commands.append(command)
        if command == ["docker", "compose", "config", "--services"]:
            return _CompletedProcess(command, stdout="postgres\nflask-app\nauth-service\ngame-service\n")
        if command == ["docker", "compose", "run", "--rm", "flask-app", "alembic", "upgrade", "head"]:
            raise subprocess.CalledProcessError(returncode=2, cmd=command)
        raise AssertionError(f"Unexpected command: {command}")

    with pytest.raises(SystemExit) as exc:
        run_startup(["--detach"], run_command=fake_run)

    assert exc.value.code == 2
    assert recorded_commands == [
        ["docker", "compose", "config", "--services"],
        ["docker", "compose", "run", "--rm", "flask-app", "alembic", "upgrade", "head"],
    ]


def test_run_startup_rejects_missing_flask_app_service_before_migrating():
    recorded_commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs):
        recorded_commands.append(command)
        if command == ["docker", "compose", "config", "--services"]:
            return _CompletedProcess(command, stdout="postgres\nauth-service\ngame-service\n")
        raise AssertionError(f"Unexpected command: {command}")

    with pytest.raises(ServiceVerificationError):
        run_startup([], run_command=fake_run)

    assert recorded_commands == [["docker", "compose", "config", "--services"]]


def test_start_stack_shell_script_runs_full_startup_flow_with_fake_docker(tmp_path):
    log_file = tmp_path / "docker.log"
    docker_path = tmp_path / "docker"
    docker_path.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_DOCKER_LOG\"\n"
        "if [ \"$#\" -eq 3 ] && [ \"$1 $2 $3\" = \"compose config --services\" ]; then\n"
        "  printf 'postgres\\nflask-app\\nauth-service\\ngame-service\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$#\" -eq 7 ] && [ \"$1 $2 $3 $4 $5 $6 $7\" = \"compose run --rm flask-app alembic upgrade head\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$#\" -eq 3 ] && [ \"$1 $2 $3\" = \"compose up --detach\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 99\n",
        encoding="utf-8",
    )
    docker_path.chmod(0o755)

    script_path = Path(__file__).resolve().parents[2] / "scripts" / "start-stack.sh"
    env = {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "FAKE_DOCKER_LOG": str(log_file),
    }

    result = subprocess.run(
        ["bash", str(script_path), "--detach"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert log_file.read_text(encoding="utf-8").splitlines() == [
        "compose config --services",
        "compose run --rm flask-app alembic upgrade head",
        "compose up --detach",
    ]


def test_start_stack_shell_script_stops_before_compose_up_when_migration_fails(tmp_path):
    log_file = tmp_path / "docker.log"
    docker_path = tmp_path / "docker"
    docker_path.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_DOCKER_LOG\"\n"
        "if [ \"$#\" -eq 3 ] && [ \"$1 $2 $3\" = \"compose config --services\" ]; then\n"
        "  printf 'postgres\\nflask-app\\nauth-service\\ngame-service\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$#\" -eq 7 ] && [ \"$1 $2 $3 $4 $5 $6 $7\" = \"compose run --rm flask-app alembic upgrade head\" ]; then\n"
        "  exit 9\n"
        "fi\n"
        "if [ \"$#\" -eq 3 ] && [ \"$1 $2 $3\" = \"compose up --detach\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 99\n",
        encoding="utf-8",
    )
    docker_path.chmod(0o755)

    script_path = Path(__file__).resolve().parents[2] / "scripts" / "start-stack.sh"
    env = {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "FAKE_DOCKER_LOG": str(log_file),
    }

    result = subprocess.run(
        ["bash", str(script_path), "--detach"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 9
    assert log_file.read_text(encoding="utf-8").splitlines() == [
        "compose config --services",
        "compose run --rm flask-app alembic upgrade head",
    ]
