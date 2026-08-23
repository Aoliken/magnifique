"""Compose startup gate for migration-first application boot."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence

COMPOSE_SERVICE_NAME = "flask-app"
DOCKER_COMPOSE_PREFIX = ["docker", "compose"]
MIGRATION_COMMAND = [*DOCKER_COMPOSE_PREFIX, "run", "--rm", COMPOSE_SERVICE_NAME, "alembic", "upgrade", "head"]


class ServiceVerificationError(RuntimeError):
    """Raised when the Compose baseline does not define the migration owner service."""


def _compose_services(run_command: Callable[..., object]) -> set[str]:
    result = run_command(
        [*DOCKER_COMPOSE_PREFIX, "config", "--services"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _verify_migration_service(run_command: Callable[..., object]) -> None:
    services = _compose_services(run_command)
    if COMPOSE_SERVICE_NAME not in services:
        raise ServiceVerificationError(
            f"Compose service '{COMPOSE_SERVICE_NAME}' is required before startup gating can run. "
            f"Available services: {', '.join(sorted(services)) or 'none'}"
        )


def run_startup(compose_args: Sequence[str], run_command: Callable[..., object] = subprocess.run) -> int:
    _verify_migration_service(run_command)
    try:
        run_command(MIGRATION_COMMAND, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc

    up_command = [*DOCKER_COMPOSE_PREFIX, "up", *compose_args]
    try:
        run_command(up_command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return run_startup(args)
    except ServiceVerificationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
