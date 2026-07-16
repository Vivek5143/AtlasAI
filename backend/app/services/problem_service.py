"""Problem service layer."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.models.problem import Problem
from app.repositories.problem_repository import ProblemRepository
from sqlalchemy.orm import Session


class ProblemService:
    """Business logic for problem operations."""

    def __init__(self, repository: ProblemRepository | Session, logger: logging.Logger | None = None) -> None:
        """Initialize the service.

        Args:
            repository: Problem repository instance or SQLAlchemy session.
            logger: Optional logger instance.
        """

        self.repository = repository if isinstance(repository, ProblemRepository) else ProblemRepository(repository)
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_all_problems(self) -> list[Problem]:
        """Return all problems."""

        self.logger.debug("Fetching all problems.")
        return self.repository.get_all()

    def get_problem(self, problem_id: UUID) -> Problem | None:
        """Return a problem by identifier."""

        self.logger.debug("Fetching problem %s.", problem_id)
        return self.repository.get_by_id(problem_id)

    def search_problems(self, keyword: str) -> list[Problem]:
        """Search problems by keyword."""

        if not keyword or not keyword.strip():
            return []

        self.logger.debug("Searching problems with keyword '%s'.", keyword)
        return self.repository.search(keyword)

    def get_problems_by_category(self, category: str) -> list[Problem]:
        """Return problems by category."""

        if not category or not category.strip():
            return []

        self.logger.debug("Fetching problems for category '%s'.", category)
        return self.repository.get_by_category(category)

    def get_problems_by_severity(self, severity: str) -> list[Problem]:
        """Return problems by severity."""

        if not severity or not severity.strip():
            return []

        self.logger.debug("Fetching problems for severity '%s'.", severity)
        return self.repository.get_by_severity(severity)

    def get_company_problems(self, company_id: UUID) -> list[Problem]:
        """Return problems associated with a company."""

        self.logger.debug("Fetching problems for company %s.", company_id)
        return self.repository.get_by_company(company_id)

    def _build_problem(self, problem_data: Problem | dict[str, Any]) -> Problem:
        """Build a Problem ORM object from input data."""

        if isinstance(problem_data, Problem):
            return problem_data

        if not problem_data.get("name"):
            raise ValueError("name is required to create a problem.")

        return Problem(**problem_data)

    def create_problem(self, problem_data: Problem | dict[str, Any]) -> Problem:
        """Create a problem."""

        problem = self._build_problem(problem_data)
        self.logger.info("Creating problem '%s'.", problem.name)
        return self.repository.create(problem)

    def update_problem(self, problem_id: UUID, updates: dict[str, Any]) -> Problem:
        """Update a problem."""

        problem = self.repository.get_by_id(problem_id)
        if problem is None:
            raise LookupError(f"Problem '{problem_id}' not found.")

        for field_name, field_value in updates.items():
            if hasattr(problem, field_name):
                setattr(problem, field_name, field_value)

        self.logger.info("Updating problem '%s'.", problem_id)
        return self.repository.update(problem)

    def delete_problem(self, problem_id: UUID) -> bool:
        """Delete a problem by identifier."""

        self.logger.info("Deleting problem '%s'.", problem_id)
        deleted = self.repository.delete(problem_id)
        if not deleted:
            raise LookupError(f"Problem '{problem_id}' not found.")
        return deleted

    def problem_statistics(self) -> dict[str, int]:
        """Return basic problem statistics."""

        problems = self.repository.get_all()
        return {
            "total_problems": self.repository.count(),
            "problems_with_category": sum(1 for problem in problems if problem.category),
            "problems_with_severity": sum(1 for problem in problems if problem.severity),
        }
