"""Shared timestamp helpers for SQLAlchemy model defaults."""

from datetime import UTC, datetime


def utc_now():
    """Return the current UTC instant without using deprecated utcnow()."""
    return datetime.now(UTC).replace(tzinfo=None)
