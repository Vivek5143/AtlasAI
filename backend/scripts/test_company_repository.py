from app.database.session import SessionLocal
from app.repositories.company_repository import CompanyRepository

db = SessionLocal()

repo = CompanyRepository(db)

print("Total Companies:", repo.count())

companies = repo.get_all()

print("Fetched:", len(companies))

print(companies[0].vendor_name)

db.close()