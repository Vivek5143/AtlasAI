from app.clients.news_api_client import NewsApiClient

client = NewsApiClient()

articles = client.fetch_company_news("SAP")

print(f"Articles Found: {len(articles)}")

if articles:
    print(articles[0])