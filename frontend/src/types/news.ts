export interface NewsArticle {
  company_id: string;
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
