"""Problem repository for database operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.problem import Problem
from app.models.problem_company_mapping import ProblemCompanyMapping


class ProblemRepository:
    """Repository for problem database operations only."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Active SQLAlchemy session.
        """

        self.session = session

    def _problem_query(self):
        """Build a problem query with eager-loaded relationships."""

        return select(Problem).options(
            selectinload(Problem.company_mappings).selectinload(ProblemCompanyMapping.company),
        )

    def get_all(self) -> list[Problem]:
        """Return all problems ordered by name."""

        statement = self._problem_query().order_by(Problem.name.asc())
        return list(self.session.execute(statement).scalars().all())

    def get_by_id(self, problem_id: UUID) -> Problem | None:
        """Return a problem by primary key."""

        statement = self._problem_query().where(Problem.id == problem_id)
        return self.session.execute(statement).scalars().first()

    def get_by_name(self, name: str) -> Problem | None:
        """Return a problem by exact name match."""

        statement = self._problem_query().where(func.lower(Problem.name) == name.strip().lower())
        return self.session.execute(statement).scalars().first()

    def search(self, keyword: str) -> list[Problem]:
        """Search problems by key text fields."""

        pattern = f"%{keyword.strip()}%"
        statement = (
            self._problem_query()
            .where(
                or_(
                    Problem.external_problem_id.ilike(pattern),
                    Problem.category.ilike(pattern),
                    Problem.name.ilike(pattern),
                    Problem.problem_type.ilike(pattern),
                    Problem.vc_stage.ilike(pattern),
                    Problem.severity.ilike(pattern),
                    Problem.financial_impact.ilike(pattern),
                    Problem.regulatory_trigger.ilike(pattern),
                    Problem.ai_solution.ilike(pattern),
                )
            )
            .order_by(Problem.name.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    def get_by_category(self, category: str) -> list[Problem]:
        """Return problems by category."""

        statement = self._problem_query().where(func.lower(Problem.category) == category.strip().lower()).order_by(Problem.name.asc())
        return list(self.session.execute(statement).scalars().all())

    def get_by_severity(self, severity: str) -> list[Problem]:
        """Return problems by severity."""

        statement = self._problem_query().where(func.lower(Problem.severity) == severity.strip().lower()).order_by(Problem.name.asc())
        return list(self.session.execute(statement).scalars().all())

    def get_by_company(self, company_id: UUID) -> list[Problem]:
        """Return problems associated with a company."""

        statement = (
            self._problem_query()
            .join(Problem.company_mappings)
            .where(ProblemCompanyMapping.company_id == company_id)
            .order_by(Problem.name.asc())
            .distinct()
        )
        return list(self.session.execute(statement).scalars().all())

    def create(self, problem: Problem) -> Problem:
        """Persist a new problem."""

        self.session.add(problem)
        self.session.commit()
        self.session.refresh(problem)
        return problem

    def update(self, problem: Problem) -> Problem:
        """Persist problem changes."""

        merged_problem = self.session.merge(problem)
        self.session.commit()
        self.session.refresh(merged_problem)
        return merged_problem

    def delete(self, problem_id: UUID) -> bool:
        """Delete a problem by identifier."""

        statement = delete(Problem).where(Problem.id == problem_id)
        result = self.session.execute(statement)
        self.session.commit()
        return (result.rowcount or 0) > 0

    def count(self) -> int:
        """Return the total number of problems."""

        statement = select(func.count()).select_from(Problem)
        return int(self.session.execute(statement).scalar_one())
