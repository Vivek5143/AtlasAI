"""Script to import sectors into the database."""

from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.sectors import SectorIngestion


def main() -> None:
    """Run the sector ingestion pipeline."""

    session = SessionLocal()

    try:
        ingestion = SectorIngestion(
            session=session,
            source=Path("data/raw/sectors_reference.csv"),
            # If you kept the CSV in data/ instead of data/raw/,
            # use: Path("data/sectors_reference.csv")
        )

        result = ingestion.run()

        print("\n========== IMPORT SUMMARY ==========")
        print(result)
        print("====================================")

    finally:
        session.close()


if __name__ == "__main__":
    main()