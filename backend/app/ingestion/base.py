"""Base classes and shared exceptions for dataset ingestion workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session


class IngestionError(Exception):
    """Base exception for all ingestion-related failures."""


class IngestionConfigurationError(IngestionError):
    """Raised when an ingestion pipeline is configured incorrectly."""


class DataValidationError(IngestionError):
    """Raised when a dataset fails structural or semantic validation."""


class DatabasePersistenceError(IngestionError):
    """Raised when cleaned dataset rows cannot be persisted safely."""


class IngestionNotImplementedError(IngestionError):
    """Raised for boilerplate methods whose business logic is not implemented yet."""


@dataclass(slots=True, frozen=True)
class IngestionResult:
    """Summarizes the outcome of a dataset ingestion run.

    Attributes:
        dataset_name: Logical name of the dataset that was processed.
        source: Source path that was used during the run.
        rows_loaded: Number of rows loaded from the source dataset.
        rows_processed: Number of rows remaining after cleaning and transformation.
        rows_saved: Number of rows written to the database.
    """

    dataset_name: str
    source: Path
    rows_loaded: int
    rows_processed: int
    rows_saved: int


class BaseIngestion(ABC):
    """Base orchestration class for CSV-to-database ingestion pipelines.

    Subclasses are responsible for providing dataset-specific loading,
    transformation, and persistence logic while this base class standardizes
    logging, validation flow, and execution lifecycle.

    Args:
        session: Active SQLAlchemy session used for persistence work.
        source: Path to the dataset source file.
        logger: Optional logger instance. A module/class-specific logger is
            created automatically when one is not provided.

    Raises:
        IngestionConfigurationError: If the source path is empty or invalid.
    """

    dataset_name: str = "dataset"
    required_columns: tuple[str, ...] = ()

    def __init__(
        self,
        session: Session,
        source: str | Path,
        logger: logging.Logger | None = None,
    ) -> None:
        if not source:
            raise IngestionConfigurationError(
                "An ingestion source path must be provided."
            )

        self.session = session
        self.source = Path(source)
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def load_dataframe(self) -> pd.DataFrame:
        """Load raw dataset records into a DataFrame.

        Returns:
            pd.DataFrame: Raw records loaded from the configured source.

        Raises:
            IngestionError: If the source cannot be read successfully.
        """

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the raw dataset before any cleaning occurs.

        Subclasses should extend this method to enforce dataset-specific rules,
        required headers, and shape checks.

        Args:
            dataframe: Raw dataset to validate.

        Raises:
            DataValidationError: If the dataset is structurally invalid.
        """

        self.logger.debug(
            "Running base validation for %s with %s rows.",
            self.dataset_name,
            len(dataframe.index),
        )

    def clean_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply non-destructive cleaning rules to the dataset.

        Args:
            dataframe: Raw or lightly validated dataset.

        Returns:
            pd.DataFrame: Cleaned dataset ready for transformation.
        """

        self.logger.debug("No default cleaning rules defined for %s.", self.dataset_name)
        return dataframe.copy()

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Transform cleaned dataset rows into persistence-ready records.

        Args:
            dataframe: Cleaned dataset.

        Returns:
            pd.DataFrame: Transformed dataset aligned to persistence needs.
        """

        self.logger.debug(
            "No default transformation rules defined for %s.",
            self.dataset_name,
        )
        return dataframe.copy()

    @abstractmethod
    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist transformed records to the database.

        Args:
            dataframe: Transformed dataset ready for persistence.

        Returns:
            int: Number of rows saved successfully.

        Raises:
            DatabasePersistenceError: If records cannot be persisted safely.
        """

    def run(self) -> IngestionResult:
        """Execute the full ingestion workflow.

        Returns:
            IngestionResult: Summary of the completed ingestion run.

        Raises:
            IngestionError: If any phase of the pipeline fails.
        """

        self.logger.info(
            "Starting %s ingestion from source '%s'.",
            self.dataset_name,
            self.source,
        )

        try:
            raw_dataframe = self.load_dataframe()
            rows_loaded = len(raw_dataframe.index)

            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)
            rows_processed = len(transformed_dataframe.index)
            rows_saved = self.save_to_database(transformed_dataframe)
        except IngestionError:
            self.logger.exception(
                "Ingestion failed for dataset '%s'.",
                self.dataset_name,
            )
            raise
        except Exception as exc:
            self.logger.exception(
                "Unexpected error while ingesting dataset '%s'.",
                self.dataset_name,
            )
            raise IngestionError(
                f"Unexpected failure during {self.dataset_name} ingestion."
            ) from exc

        result = IngestionResult(
            dataset_name=self.dataset_name,
            source=self.source,
            rows_loaded=rows_loaded,
            rows_processed=rows_processed,
            rows_saved=rows_saved,
        )

        self.logger.info(
            "Completed %s ingestion: loaded=%s processed=%s saved=%s.",
            result.dataset_name,
            result.rows_loaded,
            result.rows_processed,
            result.rows_saved,
        )
        return result

    def get_context(self) -> dict[str, Any]:
        """Return structured logging context for subclasses.

        Returns:
            dict[str, Any]: Context values that can be attached to log records.
        """

        return {
            "dataset_name": self.dataset_name,
            "source": str(self.source),
        }
