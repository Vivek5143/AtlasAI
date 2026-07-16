"""Reusable ingestion package for dataset imports into AtlasAI."""

from app.ingestion.base import (
    BaseIngestion,
    DataValidationError,
    DatabasePersistenceError,
    IngestionConfigurationError,
    IngestionError,
    IngestionNotImplementedError,
    IngestionResult,
)
from app.ingestion.companies import CompanyIngestion
from app.ingestion.mappings import CompanySectorIngestion, MappingIngestion
from app.ingestion.news import NewsIngestion
from app.ingestion.problems import ProblemIngestion
from app.ingestion.sectors import SectorIngestion

__all__ = [
    "BaseIngestion",
    "CompanyIngestion",
    "DataValidationError",
    "DatabasePersistenceError",
    "IngestionConfigurationError",
    "IngestionError",
    "IngestionNotImplementedError",
    "IngestionResult",
    "CompanySectorIngestion",
    "MappingIngestion",
    "NewsIngestion",
    "ProblemIngestion",
    "SectorIngestion",
]
