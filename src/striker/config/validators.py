"""Configuration validators — physical quantity range checks."""

from typing import Any

from pydantic import field_validator


def _positive_int(field_name: str) -> Any:
    """Return a ``@field_validator`` that enforces *field_name* > 0 (int)."""
    return field_validator(field_name)(lambda v: _check_positive(v, field_name))


def _positive_float(field_name: str) -> Any:
    """Return a ``@field_validator`` that enforces *field_name* > 0 (float)."""
    return field_validator(field_name)(lambda v: _check_positive(v, field_name))


def _check_positive(v: int | float, field_name: str) -> int | float:
    if v <= 0:
        msg = f"{field_name} must be positive, got {v}"
        raise ValueError(msg)
    return v
