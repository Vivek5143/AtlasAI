from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.problems import ProblemIngestion


def main() -> None:
    session = SessionLocal()

    try:
        ingestion = ProblemIngestion(
            session=session,
            source=Path("data/raw/problems_germany.csv"),
        )

        result = ingestion.run()

        print("\n========== IMPORT SUMMARY ==========")
        print(result)
        print("====================================")

    finally:
        session.close()


if __name__ == "__main__":
    main()