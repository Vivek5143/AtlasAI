export interface NewsArticle {
  company_id: string;
  company_name?: string | null;
  description?: string | null;
  title: string;
  url: string;
  published_at: string;
  id: string;
  created_at: string;
  updated_at: string;
}

export interface NewsListResponse {
  items: NewsArticle[];
  total: number;
}

export interface NewsRefreshSummary {
  companies_checked: number;
  companies_total: number;
  rotation_offset: number;
  articles_fetched: number;
  articles_created: number;
  articles_updated: number;
  articles_skipped: number;
  articles_duplicates: number;
  articles_rejected_irrelevant: number;
  skip_reasons: Record<string, number>;
  rag_news_indexed: number;
  rag_indexing_status: string;
}
