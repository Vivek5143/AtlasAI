from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.mappings import CompanySectorIngestion


def main():
    session = SessionLocal()

    try:
        ingestion = CompanySectorIngestion(
            session=session,
            source=Path("data/raw/companies_germany.csv"),
        )

        result = ingestion.run()
        print(result)

    finally:
        session.close()


if __name__ == "__main__":
    main()