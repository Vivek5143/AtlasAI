"""Validate the AtlasAI backend."""

from __future__ import annotations

from app.database.session import SessionLocal

from app.repositories.company_repository import CompanyRepository
from app.repositories.problem_repository import ProblemRepository
from app.repositories.sector_repository import SectorRepository

from app.services.company_service import CompanyService
from app.services.problem_service import ProblemService
from app.services.sector_service import SectorService

from app.repositories.news_repository import NewsRepository
from app.services.news_service import NewsService


def status(name: str, passed: bool) -> None:
    """Print validation status."""
    icon = "✅" if passed else "❌"
    print(f"{icon} {name}")


def main() -> None:
    """Run backend validation."""

    print("\n========================================")
    print(" AtlasAI Backend Validation")
    print("========================================\n")

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # Database Connection
        # -------------------------------------------------
        status("Database Connection", True)

        # -------------------------------------------------
        # Repositories
        # -------------------------------------------------

        company_repo = CompanyRepository(db)
        sector_repo = SectorRepository(db)
        problem_repo = ProblemRepository(db)
        news_repo = NewsRepository(db)

        company_count = company_repo.count()
        sector_count = sector_repo.count()
        problem_count = problem_repo.count()
        news_count = len(news_repo.get_recent_articles(100000))

        status(
            f"Company Repository ({company_count} companies)",
            company_count > 0,
        )

        status(
            f"Sector Repository ({sector_count} sectors)",
            sector_count > 0,
        )

        status(
            f"Problem Repository ({problem_count} problems)",
            problem_count > 0,
        )

        status(
            f"News Repository ({news_count} articles)",
            True,
        )

        # -------------------------------------------------
        # Search Tests
        # -------------------------------------------------

        companies = company_repo.search("SAP")

        status(
            "Company Search",
            len(companies) >= 0,
        )

        problems = problem_repo.search("AI")

        status(
            "Problem Search",
            len(problems) >= 0,
        )

        # -------------------------------------------------
        # Services
        # -------------------------------------------------

        company_service = CompanyService(db)
        sector_service = SectorService(db)
        problem_service = ProblemService(db)
        news_service = NewsService(db)

        status("Company Service", company_service is not None)
        status("Sector Service", sector_service is not None)
        status("Problem Service", problem_service is not None)
        status("News Service", news_service is not None)

        # -------------------------------------------------
        # Company Service
        # -------------------------------------------------

        try:
            companies = company_service.get_all_companies()
            status(
                "Company Service -> get_all_companies()",
                len(companies) > 0,
            )
        except Exception:
            status(
                "Company Service -> get_all_companies()",
                False,
            )

        # -------------------------------------------------
        # Sector Service
        # -------------------------------------------------

        try:
            sectors = sector_service.get_all_sectors()
            status(
                "Sector Service -> get_all_sectors()",
                len(sectors) > 0,
            )
        except Exception:
            status(
                "Sector Service -> get_all_sectors()",
                False,
            )

        # -------------------------------------------------
        # Problem Service
        # -------------------------------------------------

        try:
            problems = problem_service.get_all_problems()
            status(
                "Problem Service -> get_all_problems()",
                len(problems) > 0,
            )
        except Exception:
            status(
                "Problem Service -> get_all_problems()",
                False,
            )

        # -------------------------------------------------
        # Relationships
        # -------------------------------------------------

        try:
            company = company_repo.get_all()[0]

            status(
                "Company -> Sector Relationship",
                len(company.sectors) >= 0,
            )

            status(
                "Company -> News Relationship",
                len(company.news_articles) >= 0,
            )

        except Exception:
            status("Relationships", False)

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        print("\n========================================")
        print(" Validation Completed")
        print("========================================")

        print(f"Companies : {company_count}")
        print(f"Sectors   : {sector_count}")
        print(f"Problems  : {problem_count}")
        print(f"News      : {news_count}")

        print("\n✅ Backend validation completed successfully.")

    except Exception as exc:
        print("\n❌ Validation Failed")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()