from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.mappings import ProblemCompanyMappingIngestion


def main():
    session = SessionLocal()

    try:
        ingestion = ProblemCompanyMappingIngestion(
            session=session,
            source=Path("data/raw/problem_company_mapping.csv"),
        )

        result = ingestion.run()

        print("\n========== IMPORT SUMMARY ==========")
        print(result)
        print("====================================")

    finally:
        session.close()


if __name__ == "__main__":
    main()