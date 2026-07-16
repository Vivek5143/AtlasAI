"""Shared utility helpers for ingestion pipelines."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse, urlunparse


def normalize_whitespace(value: str | None) -> str | None:
    """Collapse repeated whitespace into single spaces.

    Args:
        value: Input string to normalize.

    Returns:
        str | None: Whitespace-normalized string, or ``None`` when input is null.
    """

    if value is None:
        return None

    return " ".join(value.split())


def clean_text(value: str | None) -> str | None:
    """Trim and normalize a text value.

    Args:
        value: Input string to clean.

    Returns:
        str | None: Cleaned string, or ``None`` when the result is empty.
    """

    if value is None:
        return None

    cleaned_value = normalize_whitespace(value.strip())
    return cleaned_value or None


def normalize_url(value: str | None) -> str | None:
    """Normalize a URL into a more consistent canonical form.

    Args:
        value: Input URL string.

    Returns:
        str | None: Normalized URL, or ``None`` when the value is empty.
    """

    cleaned_value = clean_text(value)
    if cleaned_value is None:
        return None

    parsed = urlparse(cleaned_value)
    if not parsed.scheme:
        parsed = urlparse(f"https://{cleaned_value}")

    normalized_netloc = parsed.netloc.lower()
    normalized_path = parsed.path.rstrip("/")
    return urlunparse(
        (
            parsed.scheme.lower(),
            normalized_netloc,
            normalized_path,
            "",
            parsed.query,
            "",
        )
    )


def parse_date(value: str | datetime | None) -> datetime | None:
    """Parse a supported date value into a ``datetime``.

    Args:
        value: Input date string or datetime.

    Returns:
        datetime | None: Parsed datetime when successful, otherwise ``None``.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    cleaned_value = clean_text(value)
    if cleaned_value is None:
        return None

    supported_formats = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
    )

    for fmt in supported_formats:
        try:
            return datetime.strptime(cleaned_value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(cleaned_value)
    except ValueError:
        return None


def safe_float(value: object, default: float | None = None) -> float | None:
    """Safely coerce a value to ``float``.

    Args:
        value: Input value to convert.
        default: Fallback value when conversion fails.

    Returns:
        float | None: Parsed float or the provided default.
    """

    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: object, default: int | None = None) -> int | None:
    """Safely coerce a value to ``int``.

    Args:
        value: Input value to convert.
        default: Fallback value when conversion fails.

    Returns:
        int | None: Parsed integer or the provided default.
    """

    if value is None or value == "":
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default
