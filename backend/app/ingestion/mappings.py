"""Company-sector mapping ingestion."""

from __future__ import annotations

import re
import uuid
from time import perf_counter
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from app.ingestion.base import BaseIngestion, DatabasePersistenceError, IngestionError
from app.ingestion.validators import (
    validate_dataframe_not_empty,
    validate_required_columns,
)
from app.models.company import Company
from app.models.company_sector import CompanySector
from app.models.problem import Problem
from app.models.problem_company_mapping import ProblemCompanyMapping
from app.models.sector import Sector


class CompanySectorIngestion(BaseIngestion):
    """Ingestion workflow for company-sector mapping datasets."""

    dataset_name = "company_sectors"
    required_columns = (
        "Vendor Name",
        "Seg Tags",
    )

    companies_source = Path("data/raw/companies_germany.csv")
    sectors_source = Path("data/raw/sectors_reference.csv")

    def load_dataframe(self) -> pd.DataFrame:
        """Load the company dataset into a DataFrame."""

        self.logger.info(
            "Preparing to load company-sector mapping dataset from '%s'.",
            self.source,
        )
        return pd.read_csv(self.source, encoding="utf-8-sig")

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the source company dataset structure."""

        super().validate_dataframe(dataframe)
        validate_dataframe_not_empty(dataframe)
        validate_required_columns(dataframe, self.required_columns)

    def _normalize_value(self, value: object) -> str | None:
        """Normalize a CSV cell into a trimmed string or ``None``."""

        if pd.isna(value):
            return None

        cleaned_value = str(value).strip()
        return cleaned_value or None

    def _load_segment_lookup(self) -> dict[str, str]:
        """Build a segment-number-to-name lookup from the sector reference CSV."""

        sector_reference = pd.read_csv(self.sectors_source, encoding="utf-8-sig")
        validate_dataframe_not_empty(sector_reference)
        validate_required_columns(sector_reference, ("Seg No.", "Segment Name"))

        segment_lookup: dict[str, str] = {}
        for row in sector_reference.to_dict(orient="records"):
            segment_number = self._normalize_value(row.get("Seg No."))
            segment_name = self._normalize_value(row.get("Segment Name"))
            if segment_number is None or segment_name is None:
                continue
            segment_lookup[segment_number] = segment_name

        return segment_lookup

    def clean_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply company-sector-specific cleaning rules."""

        cleaned_dataframe = dataframe.copy()
        for column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = cleaned_dataframe[column].map(
                self._normalize_value
            )

        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Vendor Name"].notna()
        ].copy()
        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Seg Tags"].notna()
        ].copy()
        return cleaned_dataframe

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return the cleaned company-sector source rows."""

        return dataframe.copy()

    def _load_company_lookup(self) -> dict[str, uuid.UUID]:
        """Load company IDs indexed by vendor name."""

        rows = self.session.execute(select(Company.id, Company.vendor_name)).all()
        return {
            vendor_name: company_id
            for company_id, vendor_name in rows
            if vendor_name is not None
        }

    def _load_sector_lookup(self) -> dict[str, uuid.UUID]:
        """Load sector IDs indexed by sector name."""

        rows = self.session.execute(select(Sector.id, Sector.name)).all()
        return {
            sector_name: sector_id
            for sector_id, sector_name in rows
            if sector_name is not None
        }

    def _load_existing_pairs(self) -> set[tuple[uuid.UUID, uuid.UUID]]:
        """Load already persisted company-sector pairs."""

        rows = self.session.execute(
            select(CompanySector.company_id, CompanySector.sector_id)
        ).all()
        return {(company_id, sector_id) for company_id, sector_id in rows}

    def _prepare_mappings(
        self,
        dataframe: pd.DataFrame,
        segment_lookup: dict[str, str],
        company_lookup: dict[str, uuid.UUID],
        sector_lookup: dict[str, uuid.UUID],
        existing_pairs: set[tuple[uuid.UUID, uuid.UUID]],
    ) -> tuple[list[CompanySector], int, int, int]:
        """Build CompanySector ORM objects while counting duplicates and failures."""

        staged_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
        mappings_to_insert: list[CompanySector] = []
        total_mappings = 0
        duplicates = 0
        failed = 0

        for row in dataframe.to_dict(orient="records"):
            vendor_name = row.get("Vendor Name")
            seg_tags_value = row.get("Seg Tags")

            if vendor_name is None or seg_tags_value is None:
                failed += 1
                continue

            company_id = company_lookup.get(vendor_name)
            if company_id is None:
                failed += 1
                self.logger.warning(
                    "Skipping mapping row for unknown company '%s'.",
                    vendor_name,
                )
                continue

            raw_tokens = [
                token.strip()
                for token in str(seg_tags_value).split(",")
                if token.strip()
            ]
            segment_tokens = (
                list(segment_lookup.keys())
                if any(token.upper() == "ALL" for token in raw_tokens)
                else raw_tokens
            )

            for segment_token in segment_tokens:
                total_mappings += 1
                segment_name = segment_lookup.get(segment_token)
                if segment_name is None:
                    failed += 1
                    self.logger.warning(
                        "Skipping unknown segment number '%s' for company '%s'.",
                        segment_token,
                        vendor_name,
                    )
                    continue

                sector_id = sector_lookup.get(segment_name)
                if sector_id is None:
                    failed += 1
                    self.logger.warning(
                        "Skipping unmapped sector '%s' for company '%s'.",
                        segment_name,
                        vendor_name,
                    )
                    continue

                pair = (company_id, sector_id)
                if pair in existing_pairs or pair in staged_pairs:
                    duplicates += 1
                    continue

                mappings_to_insert.append(
                    CompanySector(company_id=company_id, sector_id=sector_id)
                )
                staged_pairs.add(pair)

        return mappings_to_insert, total_mappings, duplicates, failed

    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist company-sector mappings to the database."""

        segment_lookup = self._load_segment_lookup()
        company_lookup = self._load_company_lookup()
        sector_lookup = self._load_sector_lookup()
        existing_pairs = self._load_existing_pairs()
        mappings_to_insert, _, _, _ = self._prepare_mappings(
            dataframe=dataframe,
            segment_lookup=segment_lookup,
            company_lookup=company_lookup,
            sector_lookup=sector_lookup,
            existing_pairs=existing_pairs,
        )

        if not mappings_to_insert:
            return 0

        try:
            self.session.add_all(mappings_to_insert)
            self.session.commit()
            return len(mappings_to_insert)
        except Exception as exc:
            self.session.rollback()
            raise DatabasePersistenceError(
                "Failed to persist company-sector mappings to the database."
            ) from exc

    def run(self) -> dict[str, int]:
        """Execute the company-sector ingestion workflow."""

        start_time = perf_counter()
        total_companies = 0
        total_mappings = 0
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
            total_companies = len(raw_dataframe.index)

            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)

            segment_lookup = self._load_segment_lookup()
            company_lookup = self._load_company_lookup()
            sector_lookup = self._load_sector_lookup()
            existing_pairs = self._load_existing_pairs()
            mappings_to_insert, total_mappings, duplicates, failed = self._prepare_mappings(
                dataframe=transformed_dataframe,
                segment_lookup=segment_lookup,
                company_lookup=company_lookup,
                sector_lookup=sector_lookup,
                existing_pairs=existing_pairs,
            )

            if mappings_to_insert:
                try:
                    self.session.add_all(mappings_to_insert)
                    self.session.commit()
                    inserted = len(mappings_to_insert)
                except Exception as exc:
                    self.session.rollback()
                    failed += len(mappings_to_insert)
                    raise DatabasePersistenceError(
                        "Failed to persist company-sector mappings to the database."
                    ) from exc

            elapsed_seconds = perf_counter() - start_time
            self.logger.info(
                "Company-sector ingestion complete: total_companies=%s total_mappings=%s inserted=%s duplicates=%s failed=%s elapsed_seconds=%.3f.",
                total_companies,
                total_mappings,
                inserted,
                duplicates,
                failed,
                elapsed_seconds,
            )
            return {
                "total_companies": total_companies,
                "total_mappings": total_mappings,
                "inserted": inserted,
                "duplicates": duplicates,
                "failed": failed,
            }
        except IngestionError:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Company-sector ingestion failed after %.3f seconds.",
                elapsed_seconds,
            )
            raise
        except Exception as exc:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Unexpected error while ingesting company-sector mappings after %.3f seconds.",
                elapsed_seconds,
            )
            raise IngestionError(
                "Unexpected failure during company-sector mapping ingestion."
            ) from exc


MappingIngestion = CompanySectorIngestion


class ProblemCompanyMappingIngestion(BaseIngestion):
    """Ingestion workflow for problem-company mapping datasets."""

    dataset_name = "problem_company_mappings"
    required_columns = (
        "Problem Statement",
        "Germany Vendors (ranked)",
        "ROI Benchmark",
        "Payback (months)",
        "Regulatory Benefit",
    )

    source_path = Path("data/raw/problem_company_mapping.csv")

    def load_dataframe(self) -> pd.DataFrame:
        """Load the source problem-company mapping CSV into a DataFrame."""

        self.logger.info(
            "Preparing to load problem-company mapping dataset from '%s'.",
            self.source,
        )
        return pd.read_csv(self.source, encoding="utf-8-sig")

    def validate_dataframe(self, dataframe: pd.DataFrame) -> None:
        """Validate the problem-company mapping dataset structure."""

        super().validate_dataframe(dataframe)
        validate_dataframe_not_empty(dataframe)
        validate_required_columns(dataframe, self.required_columns)

    def _normalize_value(self, value: object) -> str | None:
        """Normalize a CSV cell into a trimmed string or ``None``."""

        if pd.isna(value):
            return None

        cleaned_value = str(value).strip()
        return cleaned_value or None

    def _split_vendor_names(self, value: str | None) -> list[str]:
        """Split a vendor list into individual vendor names."""

        if value is None:
            return []

        if re.search(r"\b\d+\.\s*", value):
            tokens = re.split(r"\s*\d+\.\s*", value)
        else:
            tokens = value.split(",")

        return [token.strip() for token in tokens if token and token.strip()]

    def clean_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Apply problem-company mapping cleaning steps."""

        cleaned_dataframe = dataframe.copy()
        for column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = cleaned_dataframe[column].map(
                self._normalize_value
            )

        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Problem Statement"].notna()
        ].copy()
        cleaned_dataframe = cleaned_dataframe.loc[
            cleaned_dataframe["Germany Vendors (ranked)"].notna()
        ].copy()
        return cleaned_dataframe

    def transform_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return the cleaned mapping dataset unchanged."""

        return dataframe.copy()

    def _load_problem_lookup(self) -> dict[str, uuid.UUID]:
        """Load problem IDs indexed by problem statement."""

        rows = self.session.execute(select(Problem.id, Problem.name)).all()
        return {
            problem_name: problem_id
            for problem_id, problem_name in rows
            if problem_name is not None
        }

    def _load_company_lookup(self) -> dict[str, uuid.UUID]:
        """Load company IDs indexed by vendor name."""

        rows = self.session.execute(select(Company.id, Company.vendor_name)).all()
        return {
            vendor_name: company_id
            for company_id, vendor_name in rows
            if vendor_name is not None
        }

    def _load_existing_pairs(self) -> set[tuple[uuid.UUID, uuid.UUID]]:
        """Load already persisted problem-company pairs."""

        rows = self.session.execute(
            select(ProblemCompanyMapping.company_id, ProblemCompanyMapping.problem_id)
        ).all()
        return {(company_id, problem_id) for company_id, problem_id in rows}

    def _prepare_mappings(
        self,
        dataframe: pd.DataFrame,
        problem_lookup: dict[str, uuid.UUID],
        company_lookup: dict[str, uuid.UUID],
        existing_pairs: set[tuple[uuid.UUID, uuid.UUID]],
    ) -> tuple[list[ProblemCompanyMapping], int, int, int, int]:
        """Build ORM objects while counting duplicates, missing companies, and failures."""

        staged_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
        mappings_to_insert: list[ProblemCompanyMapping] = []
        total_rows = 0
        duplicates = 0
        missing_companies = 0
        failed = 0

        for row in dataframe.to_dict(orient="records"):
            total_rows += 1

            problem_name = row.get("Problem Statement")
            vendor_list = row.get("Germany Vendors (ranked)")

            if problem_name is None or vendor_list is None:
                failed += 1
                continue

            problem_id = problem_lookup.get(problem_name)
            if problem_id is None:
                failed += 1
                self.logger.warning(
                    "Skipping mapping row for unknown problem '%s'.",
                    problem_name,
                )
                continue

            vendor_names = self._split_vendor_names(vendor_list)
            for vendor_name in vendor_names:
                company_id = company_lookup.get(vendor_name)
                if company_id is None:
                    missing_companies += 1
                    self.logger.warning(
                        "Skipping unknown vendor '%s' for problem '%s'.",
                        vendor_name,
                        problem_name,
                    )
                    continue

                pair = (company_id, problem_id)
                if pair in existing_pairs or pair in staged_pairs:
                    duplicates += 1
                    continue

                try:
                    mappings_to_insert.append(
                        ProblemCompanyMapping(
                            company_id=company_id,
                            problem_id=problem_id,
                            roi=row.get("ROI Benchmark"),
                            payback=row.get("Payback (months)"),
                            implementation_notes=row.get("Regulatory Benefit"),
                        )
                    )
                except Exception as exc:
                    failed += 1
                    self.logger.warning(
                        "Failed to build problem-company mapping for vendor '%s' and problem '%s': %s",
                        vendor_name,
                        problem_name,
                        exc,
                    )
                    continue

                staged_pairs.add(pair)

        return mappings_to_insert, total_rows, duplicates, missing_companies, failed

    def save_to_database(self, dataframe: pd.DataFrame) -> int:
        """Persist problem-company mappings to the database."""

        problem_lookup = self._load_problem_lookup()
        company_lookup = self._load_company_lookup()
        existing_pairs = self._load_existing_pairs()
        mappings_to_insert, _, _, _, _ = self._prepare_mappings(
            dataframe=dataframe,
            problem_lookup=problem_lookup,
            company_lookup=company_lookup,
            existing_pairs=existing_pairs,
        )

        if not mappings_to_insert:
            return 0

        try:
            self.session.add_all(mappings_to_insert)
            self.session.commit()
            return len(mappings_to_insert)
        except Exception as exc:
            self.session.rollback()
            raise DatabasePersistenceError(
                "Failed to persist problem-company mappings to the database."
            ) from exc

    def run(self) -> dict[str, int]:
        """Execute the problem-company mapping ingestion workflow."""

        start_time = perf_counter()
        rows = 0
        inserted = 0
        duplicates = 0
        missing_companies = 0
        failed = 0

        self.logger.info(
            "Starting %s ingestion from source '%s'.",
            self.dataset_name,
            self.source,
        )

        try:
            raw_dataframe = self.load_dataframe()
            rows = len(raw_dataframe.index)

            self.validate_dataframe(raw_dataframe)
            cleaned_dataframe = self.clean_dataframe(raw_dataframe)
            transformed_dataframe = self.transform_dataframe(cleaned_dataframe)

            problem_lookup = self._load_problem_lookup()
            company_lookup = self._load_company_lookup()
            existing_pairs = self._load_existing_pairs()
            mappings_to_insert, _, duplicates, missing_companies, failed = self._prepare_mappings(
                dataframe=transformed_dataframe,
                problem_lookup=problem_lookup,
                company_lookup=company_lookup,
                existing_pairs=existing_pairs,
            )

            if mappings_to_insert:
                try:
                    self.session.add_all(mappings_to_insert)
                    self.session.commit()
                    inserted = len(mappings_to_insert)
                except Exception as exc:
                    self.session.rollback()
                    failed += len(mappings_to_insert)
                    raise DatabasePersistenceError(
                        "Failed to persist problem-company mappings to the database."
                    ) from exc

            elapsed_seconds = perf_counter() - start_time
            self.logger.info(
                "Problem-company mapping ingestion complete: rows=%s inserted=%s duplicates=%s missing_companies=%s failed=%s elapsed_seconds=%.3f.",
                rows,
                inserted,
                duplicates,
                missing_companies,
                failed,
                elapsed_seconds,
            )
            return {
                "rows": rows,
                "inserted": inserted,
                "duplicates": duplicates,
                "missing_companies": missing_companies,
                "failed": failed,
            }
        except IngestionError:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Problem-company mapping ingestion failed after %.3f seconds.",
                elapsed_seconds,
            )
            raise
        except Exception as exc:
            self.session.rollback()
            elapsed_seconds = perf_counter() - start_time
            self.logger.exception(
                "Unexpected error while ingesting problem-company mappings after %.3f seconds.",
                elapsed_seconds,
            )
            raise IngestionError(
                "Unexpected failure during problem-company mapping ingestion."
            ) from exc
