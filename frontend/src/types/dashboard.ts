export interface DashboardMetrics {
  total_companies: number;
  total_sectors: number;
  total_problems: number;
  total_news_articles: number;
  companies_with_sectors: number;
  companies_with_news: number;
  sectors_with_companies: number;
  problems_with_category: number;
  problems_with_severity: number;
  generated_at: string;
}

export interface DashboardResponse {
  items: DashboardMetrics[];
  total: number;
}
