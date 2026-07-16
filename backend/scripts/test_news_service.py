from app.database.session import SessionLocal
from app.services.news_service import NewsService

db = SessionLocal()

service = NewsService(db)

articles = service.sync_company_news("SAP")

print(f"Saved {len(articles)} articles")