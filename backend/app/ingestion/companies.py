"""Company dataset ingestion boilerplate."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.base import (
    BaseIngestion,
    DatabasePersistenceError,
    IngestionError,
)
from app.ingestion.utils import clean_text
from app.ingestion.validators import (
    validate_dataframe_not_empty,
    validate_required_columns,
)
from app.models.company import Company


class CompanyIngestion(BaseIngestion):
    """Ingestion workflow for company datasets."""

    dataset_name = "companies"
    required_columns = (
        "Vendor Name",
        "Country",
        "Website",
        "Company Type",
        "AI Category",
        "Funding",
        "Est. Revenue",
        "Maturity",
        "Top Deployment Evidence",
    )
    column_mapping = {
        "Vendor Name": "vendor_name",
        "Country": "country",
        "Website": "website",
        "Company Type": "company_type",
        "AI Category": "ai_category",
        "Funding": "funding",
        "Est. Revenue": "estimated_revenue",
        "Maturity": "maturity",
        "Top Deployment Evidence": "deployment_evidence",
    }

    def __init__(
        self,
        session: Session,
        source: str | Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the company ingestion workflow and counters."""

        super().__init__(session=session, source=source, logger=logger)
        self._stats: dict[str, int] = {
            "total": 0,
            "inserted": 0,
            "duplicates": 0,
            "failed": 0,
        }

    def load_dataframe(self) -> pd.DataFrame:
        """Load the source company CSV into a DataFrame.

        Returns:
            pd.DataFrame: Raw company dataset loaded from CSV.
        """

        self.logger.info("Preparing to load company dataset from '%s'.", self.source)

        dataframe = pd.read_csv(
            self.source,
            encoding="utf-8-sig",
        )
        self._stats["total"] = len(dataframe.index)
        return dataframe

    def _clean_scalar(self, value: Any) -> str | None:
        """Normalize scalar CSV values into clean strings or ``None``.

        Args:
            value: Raw CSV cell value.

        Returns:
            str | None: Cleaned string value when present.
        """

        if pd.isna(value):
            return None

        return clean_text(str(value))

    def _normalize_website(self, value: Any) -> str | None:
        """Normalize a website field to lowercase text.

        Args:
            value: Raw website field from the CSV.

        Returns:
            str | None: Lowercased website value when present.
        """

        cleaned_value = self._clean_scalar(value)
        return cleaned_value.lower() if cleaned_value is not None else None

    def _existing_vendor_names(self) -> set[str]:
        """Fetch existing company vendor names for duplicate detection.

        Returns:
            set[str]: Existing vendor names already stored in the database.
        """

        statement = select(Company.vendor_name)
        return {
            vendor_name
            for vendor_name in self.session.execute(statement).scalars().all()
            if vendor_name is not None
        }

    def _build_company(self, row: pd.Series) -> Company:
        """Create a Company ORM object from a transformed row.

        Args:
            row: Transformed company row.

        Returns:
            Company: ORM instance ready for insertion.
        """

        return Company(
            vendor_name=row["vendor_name"],
            country=row["country"],
            website=row["website"],
            company_type=row["company_type"],
            ai_category=row["ai_category"],
            funding=row["funding"],
            estimated_revenue=row["estimated_revenue"],
            maturity=row["maturity"],
            deployment_evidence=row["deployment_evidence"],
        )

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the company dataset structure before processing.

        Args:
            dataframe: Raw company dataset.
        """

        super().validate_dataframe(dataframe)
        validate_dataframe_not_empty(dataframe)
        validate_required_columns(dataframe, self.required_columns)

    def clean_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply company-specific cleaning steps.

        Args:
            dataframe: Validated company dataset.

        Returns:
            pd.DataFrame: Cleaned dataset copy.
        """

        cleaned_dataframe = dataframe.loc[:, list(self.required_columns)].copy()
        for column in self.required_columns:
            if column == "Website":
                cleaned_dataframe[column] = cleaned_dataframe[column].map(
                    self._normalize_website
                )
            else:
                cleaned_dataframe[column] = cleaned_dataframe[column].map(
                    self._clean_scalar
                )

        missing_vendor_name_mask = cleaned_dataframe["Vendor Name"].isna()
        skipped_rows = int(missing_vendor_name_mask.sum())
        if skipped_rows:
            self.logger.warning(
                "Skipping %s company rows without a vendor name.",
                skipped_rows,
            )
            self._stats["failed"] += skipped_rows
            cleaned_dataframe = cleaned_dataframe.loc[~missing_vendor_name_mask].copy()

        return cleaned_dataframe

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Transform company rows into persistence-ready records.

        Args:
            dataframe: Cleaned company dataset.

        Returns:
            pd.DataFrame: Transformed dataset copy.
        """

        transformed_dataframe = dataframe.rename(columns=self.column_mapping).copy()
        return transformed_dataframe.loc[:, list(self.column_mapping.values())]

    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist company rows to the database.

        Args:
            dataframe: Transformed company dataset.

        Returns:
            int: Number of rows saved.

        Raises:
            DatabasePersistenceError: If the transaction fails.
        """

        existing_vendor_names = self._existing_vendor_names()
        staged_vendor_names: set[str] = set()
        companies_to_insert: list[Company] = []

        for row in dataframe.itertuples(index=False):
            row_data = row._asdict()
            vendor_name = row_data["vendor_name"]

            if vendor_name in existing_vendor_names or vendor_name in staged_vendor_names:
                self._stats["duplicates"] += 1
                continue

            try:
                companies_to_insert.append(self._build_company(pd.Series(row_data)))
            except Exception as exc:
                self._stats["failed"] += 1
                self.logger.warning(
                    "Failed to build company '%s' for ingestion: %s",
                    vendor_name,
                    exc,
                )
                continue

            staged_vendor_names.add(vendor_name)

        if not companies_to_insert:
            return 0

        try:
            self.session.add_all(companies_to_insert)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            self._stats["failed"] += len(companies_to_insert)
            raise DatabasePersistenceError(
                "Failed to persist company dataset to the database."
            ) from exc

        self._stats["inserted"] = len(companies_to_insert)
        return len(companies_to_insert)

    def run(self) -> dict[str, int]:
        """Execute the company ingestion workflow and return summary metrics.

        Returns:
            dict[str, int]: Summary containing total, inserted, duplicates,
                and failed counts.
        """

        started_at = perf_counter()
        self.logger.info(
            "Starting %s ingestion from source '%s'.",
            self.dataset_name,
            self.source,
        )

        try:
            raw_dataframe = self.load_dataframe()
            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)
            self.save_to_database(transformed_dataframe)
        except IngestionError:
            elapsed_seconds = perf_counter() - started_at
            self.logger.exception(
                (
                    "Company ingestion failed after %.3f seconds: total=%s inserted=%s "
                    "duplicates=%s failed=%s."
                ),
                elapsed_seconds,
                self._stats["total"],
                self._stats["inserted"],
                self._stats["duplicates"],
                self._stats["failed"],
            )
            raise
        except Exception as exc:
            elapsed_seconds = perf_counter() - started_at
            self.logger.exception(
                (
                    "Unexpected company ingestion failure after %.3f seconds: total=%s "
                    "inserted=%s duplicates=%s failed=%s."
                ),
                elapsed_seconds,
                self._stats["total"],
                self._stats["inserted"],
                self._stats["duplicates"],
                self._stats["failed"],
            )
            raise IngestionError("Unexpected failure during company ingestion.") from exc

        elapsed_seconds = perf_counter() - started_at
        self.logger.info(
            (
                "Completed %s ingestion in %.3f seconds: total=%s inserted=%s "
                "duplicates=%s failed=%s."
            ),
            self.dataset_name,
            elapsed_seconds,
            self._stats["total"],
            self._stats["inserted"],
            self._stats["duplicates"],
            self._stats["failed"],
        )

        return dict(self._stats)
