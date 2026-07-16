"""Sector dataset ingestion boilerplate."""

from __future__ import annotations

from time import perf_counter

import pandas as pd
from sqlalchemy import select

from app.ingestion.base import BaseIngestion, DatabasePersistenceError, IngestionError
from app.ingestion.validators import (
    validate_dataframe_not_empty,
    validate_required_columns,
)
from app.models.sector import Sector


class SectorIngestion(BaseIngestion):
    """Ingestion workflow for sector datasets and company-sector mappings."""

    dataset_name = "sectors"
    required_columns = (
        "Segment Name",
        "Definition",
    )

    optional_columns = (
        "AI Adoption",
        "DE Market Size",
        "Regulatory Complexity",
        "Platform Priority",
        "Primary AI Entry Point",
        "Key Germany Companies",
    )

    def load_dataframe(self) -> pd.DataFrame:
        """Load the source sector CSV into a DataFrame.

        Returns:
            pd.DataFrame: Raw sector dataset loaded from CSV.
        """

        self.logger.info("Preparing to load sector dataset from '%s'.", self.source)

        dataframe = pd.read_csv(
            self.source,
            encoding="utf-8-sig",
        )
        return dataframe

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the sector dataset structure.

        Args:
            dataframe: Raw sector dataset.
        """

        super().validate_dataframe(dataframe)
        validate_dataframe_not_empty(dataframe)
        validate_required_columns(dataframe, self.required_columns)

    def _normalize_value(self, value: object) -> str | None:
        """Normalize a CSV cell into a trimmed string or ``None``."""

        if pd.isna(value):
            return None

        cleaned_value = str(value).strip()
        return cleaned_value or None

    def clean_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply sector-specific cleaning steps.

        Args:
            dataframe: Validated sector dataset.

        Returns:
            pd.DataFrame: Cleaned dataset copy.
        """

        cleaned_dataframe = dataframe.copy()
        for column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = cleaned_dataframe[column].map(
                self._normalize_value
            )

        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Segment Name"].notna()
        ].copy()
        return cleaned_dataframe

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Prepare normalized sectors and company-sector mappings.

        Args:
            dataframe: Cleaned sector dataset.

        Returns:
            pd.DataFrame: Transformed dataset copy.
        """

        transformed_dataframe = dataframe.loc[:, list(dataframe.columns)].copy()
        transformed_dataframe["name"] = transformed_dataframe["Segment Name"]
        transformed_dataframe["description"] = transformed_dataframe["Definition"]

        model_column_names = {
            column.name for column in Sector.__table__.columns if column.name != "id"
        }
        optional_column_mapping = {
            "AI Adoption": "ai_adoption",
            "DE Market Size": "de_market_size",
            "Regulatory Complexity": "regulatory_complexity",
            "Platform Priority": "platform_priority",
            "Primary AI Entry Point": "primary_ai_entry_point",
            "Key Germany Companies": "key_germany_companies",
        }

        for source_column, target_column in optional_column_mapping.items():
            if target_column in model_column_names and source_column in transformed_dataframe.columns:
                transformed_dataframe[target_column] = transformed_dataframe[source_column]

        return transformed_dataframe

    def _prepare_sector_records(self, dataframe: pd.DataFrame) -> tuple[list[Sector], int, int]:
        """Build Sector ORM objects and count duplicates or staging failures."""

        existing_sector_names = {
            name
            for name in self.session.execute(select(Sector.name)).scalars().all()
            if name is not None
        }

        sectors_to_insert: list[Sector] = []
        staged_sector_names: set[str] = set()
        duplicates = 0
        failed = 0

        for row in dataframe.to_dict(orient="records"):
            sector_name = row.get("name")
            if sector_name is None:
                failed += 1
                continue

            if sector_name in existing_sector_names or sector_name in staged_sector_names:
                duplicates += 1
                continue

            try:
                sector_kwargs: dict[str, object] = {"name": sector_name}
                for column_name in Sector.__table__.columns.keys():
                    if column_name in {"id", "name", "created_at", "updated_at"}:
                        continue
                    if column_name in row and row[column_name] is not None:
                        sector_kwargs[column_name] = row[column_name]

                sectors_to_insert.append(Sector(**sector_kwargs))
                staged_sector_names.add(sector_name)
            except Exception as exc:
                failed += 1
                self.logger.warning(
                    "Failed to stage sector '%s' for ingestion: %s",
                    sector_name,
                    exc,
                )

        return sectors_to_insert, duplicates, failed

    def _commit_sectors(self, sectors_to_insert: list[Sector]) -> int:
        """Persist staged Sector ORM objects in a single transaction."""

        if not sectors_to_insert:
            return 0

        try:
            self.session.add_all(sectors_to_insert)
            self.session.commit()
            return len(sectors_to_insert)
        except Exception as exc:
            self.session.rollback()
            raise DatabasePersistenceError(
                "Failed to persist sector dataset to the database."
            ) from exc

    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist sectors and association rows to the database.

        Args:
            dataframe: Transformed sector dataset.

        Returns:
            int: Number of rows saved.

        Raises:
            DatabasePersistenceError: If records cannot be persisted safely.
        """

        sectors_to_insert, _, _ = self._prepare_sector_records(dataframe)
        return self._commit_sectors(sectors_to_insert)

    def run(self) -> dict[str, int]:
        """Execute the sector ingestion workflow and return summary stats."""

        start_time = perf_counter()
        total_rows = 0
        inserted = 0
        duplicates = 0
        failed = 0

        self.logger.info(
            "Starting %s ingestion from source '%s'.",
            self.dataset_name,
            self.source,
        )

        try:
            raw_dataframe = self.load_dataframe()
            total_rows = len(raw_dataframe.index)

            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)

            sectors_to_insert, duplicates, failed = self._prepare_sector_records(
                transformed_dataframe
            )
            inserted = self._commit_sectors(sectors_to_insert)

            elapsed_seconds = perf_counter() - start_time
            self.logger.info(
                "Sector ingestion complete: total=%s inserted=%s duplicates=%s failed=%s elapsed_seconds=%.3f.",
                total_rows,
                inserted,
                duplicates,
                failed,
                elapsed_seconds,
            )
            return {
                "total": total_rows,
                "inserted": inserted,
                "duplicates": duplicates,
                "failed": failed,
            }
        except IngestionError:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Sector ingestion failed after %.3f seconds.",
                elapsed_seconds,
            )
            raise
        except Exception as exc:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Unexpected error while ingesting sector dataset after %.3f seconds.",
                elapsed_seconds,
            )
            raise IngestionError(
                "Unexpected failure during sectors ingestion."
            ) from exc
