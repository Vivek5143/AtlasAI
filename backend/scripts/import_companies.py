from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.companies import CompanyIngestion


def main():
    session = SessionLocal()

    try:
        ingestion = CompanyIngestion(
            session=session,
            source=Path("data/raw/companies_germany.csv"),
        )

        result = ingestion.run()
        print(result)

    finally:
        session.close()


if __name__ == "__main__":
    main()