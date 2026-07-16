"""Validation helpers for ingestion pipelines."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import pandas as pd

from app.ingestion.base import DataValidationError


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: Collection[str],
) -> None:
    """Validate that a DataFrame contains all required columns.

    Args:
        dataframe: Dataset to validate.
        required_columns: Required column names for the dataset.

    Raises:
        DataValidationError: If one or more required columns are missing.
    """

    missing_columns = sorted(set(required_columns) - set(dataframe.columns))
    if missing_columns:
        raise DataValidationError(
            "Dataset is missing required columns: "
            + ", ".join(missing_columns)
        )


def validate_uuid(value: UUID | str | None) -> UUID:
    """Validate and normalize a UUID value.

    Args:
        value: Candidate UUID value.

    Returns:
        UUID: Parsed UUID instance.

    Raises:
        DataValidationError: If the value is empty or malformed.
    """

    if value is None or value == "":
        raise DataValidationError("UUID value cannot be empty.")

    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise DataValidationError(f"Invalid UUID value: {value!r}") from exc


def validate_url(value: str | None) -> str:
    """Validate a URL string used during ingestion.

    Args:
        value: Candidate URL string.

    Returns:
        str: Trimmed URL string.

    Raises:
        DataValidationError: If the URL is empty or malformed.
    """

    if value is None:
        raise DataValidationError("URL value cannot be null.")

    candidate = value.strip()
    if not candidate:
        raise DataValidationError("URL value cannot be blank.")

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DataValidationError(f"Invalid URL value: {value!r}")

    return candidate


def validate_dataframe_not_empty(dataframe: pd.DataFrame) -> None:
    """Validate that a DataFrame contains at least one record.

    Args:
        dataframe: Dataset to validate.

    Raises:
        DataValidationError: If the dataset is empty.
    """

    if dataframe.empty:
        raise DataValidationError("Dataset is empty and cannot be ingested.")
