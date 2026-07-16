"""Problem dataset ingestion."""

from __future__ import annotations

from time import perf_counter

import pandas as pd
from sqlalchemy import select

from app.ingestion.base import BaseIngestion, DatabasePersistenceError, IngestionError
from app.ingestion.validators import (
    validate_dataframe_not_empty,
    validate_required_columns,
)
from app.models.problem import Problem


class ProblemIngestion(BaseIngestion):
    """Ingestion workflow for problem definition datasets."""

    dataset_name = "Problems"
    required_columns = (
        "Prob ID",
        "Category",
        "Problem Statement",
        "VC Stage",
        "Severity",
        "Financial Impact (€)",
        "Regulatory Trigger",
        "AI Use Case Solution",
        "Problem Type",
    )

    def load_dataframe(self) -> pd.DataFrame:
        """Load the source problem CSV into a DataFrame.

        Returns:
            pd.DataFrame: Raw problem dataset loaded from CSV.
        """

        self.logger.info("Preparing to load problem dataset from '%s'.", self.source)
        return pd.read_csv(
            self.source,
            encoding="utf-8-sig",
        )

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the problem dataset structure.

        Args:
            dataframe: Raw problem dataset.
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
        """Apply problem-specific cleaning steps.

        Args:
            dataframe: Validated problem dataset.

        Returns:
            pd.DataFrame: Cleaned dataset copy.
        """

        cleaned_dataframe = dataframe.copy()

        for column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = cleaned_dataframe[column].map(
                self._normalize_value
            )

        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Problem Statement"].notna()
        ].copy()
        return cleaned_dataframe

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Transform problem rows into Problem model-ready records.

        Args:
            dataframe: Cleaned problem dataset.

        Returns:
            pd.DataFrame: Transformed dataset copy.
        """

        transformed_dataframe = dataframe.rename(
            columns={
                "Prob ID": "external_problem_id",
                "Category": "category",
                "Problem Statement": "name",
                "VC Stage": "vc_stage",
                "Severity": "severity",
                "Financial Impact (€)": "financial_impact",
                "Regulatory Trigger": "regulatory_trigger",
                "AI Use Case Solution": "ai_solution",
                "Problem Type": "problem_type",
            }
        ).copy()

        return transformed_dataframe.loc[
            :, 
            [
                "external_problem_id",
                "category",
                "name",
                "vc_stage",
                "severity",
                "financial_impact",
                "regulatory_trigger",
                "ai_solution",
                "problem_type",
            ],
        ]

    def _load_existing_keys(self) -> tuple[set[str], set[str]]:
        """Load existing problem keys for duplicate detection."""

        existing_external_ids: set[str] = set()
        existing_names: set[str] = set()

        rows = self.session.execute(
            select(Problem.external_problem_id, Problem.name)
        ).all()

        for external_problem_id, name in rows:
            if external_problem_id is not None:
                existing_external_ids.add(external_problem_id)
            if name is not None:
                existing_names.add(name)

        return existing_external_ids, existing_names

    def _build_problem_objects(self, dataframe: pd.DataFrame) -> tuple[list[Problem], int, int]:
        """Build ORM objects while counting duplicates and invalid rows."""

        existing_external_ids, existing_names = self._load_existing_keys()
        staged_external_ids: set[str] = set()
        staged_names: set[str] = set()
        problems_to_insert: list[Problem] = []
        duplicates = 0
        failed = 0

        for row in dataframe.to_dict(orient="records"):
            external_problem_id = row.get("external_problem_id")
            name = row.get("name")

            if name is None:
                failed += 1
                continue

            if external_problem_id is not None and (
                external_problem_id in existing_external_ids
                or external_problem_id in staged_external_ids
            ):
                duplicates += 1
                continue

            if name in existing_names or name in staged_names:
                duplicates += 1
                continue

            try:
                problems_to_insert.append(
                    Problem(
                        external_problem_id=external_problem_id,
                        category=row.get("category"),
                        name=name,
                        vc_stage=row.get("vc_stage"),
                        severity=row.get("severity"),
                        financial_impact=row.get("financial_impact"),
                        regulatory_trigger=row.get("regulatory_trigger"),
                        ai_solution=row.get("ai_solution"),
                        problem_type=row.get("problem_type"),
                    )
                )
            except Exception as exc:
                failed += 1
                self.logger.warning(
                    "Failed to build problem '%s' for ingestion: %s",
                    name,
                    exc,
                )
                continue

            if external_problem_id is not None:
                staged_external_ids.add(external_problem_id)
            staged_names.add(name)

        return problems_to_insert, duplicates, failed

    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist problem rows to the database.

        Args:
            dataframe: Transformed problem dataset.

        Returns:
            int: Number of rows saved.

        Raises:
            DatabasePersistenceError: If the transaction fails.
        """

        problems_to_insert, _, _ = self._build_problem_objects(dataframe)

        if not problems_to_insert:
            return 0

        try:
            self.session.add_all(problems_to_insert)
            self.session.commit()
            return len(problems_to_insert)
        except Exception as exc:
            self.session.rollback()
            raise DatabasePersistenceError(
                "Failed to persist problem dataset to the database."
            ) from exc

    def run(self) -> dict[str, int]:
        """Execute the problem ingestion workflow.

        Returns:
            dict[str, int]: Summary of the completed ingestion run.
        """

        start_time = perf_counter()
        total = 0
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
            total = len(raw_dataframe.index)

            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)

            problems_to_insert, duplicates, failed = self._build_problem_objects(
                transformed_dataframe
            )

            if problems_to_insert:
                try:
                    self.session.add_all(problems_to_insert)
                    self.session.commit()
                    inserted = len(problems_to_insert)
                except Exception as exc:
                    self.session.rollback()
                    failed += len(problems_to_insert)
                    raise DatabasePersistenceError(
                        "Failed to persist problem dataset to the database."
                    ) from exc

            elapsed_seconds = perf_counter() - start_time
            self.logger.info(
                "Problem ingestion complete: total=%s inserted=%s duplicates=%s failed=%s elapsed_seconds=%.3f.",
                total,
                inserted,
                duplicates,
                failed,
                elapsed_seconds,
            )
            return {
                "total": total,
                "inserted": inserted,
                "duplicates": duplicates,
                "failed": failed,
            }
        except IngestionError:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Problem ingestion failed after %.3f seconds.",
                elapsed_seconds,
            )
            raise
        except Exception as exc:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Unexpected error while ingesting problem dataset after %.3f seconds.",
                elapsed_seconds,
            )
            raise IngestionError(
                "Unexpected failure during problems ingestion."
            ) from exc
