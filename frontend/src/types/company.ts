import type { NewsArticle } from "@/types/news";
import type { Problem } from "@/types/problem";
import type { Sector } from "@/types/sector";

export interface Company {
  id: string;
  vendor_name: string;
  country: string | null;
  website: string | null;
  company_type: string | null;
  ai_category: string | null;
  funding: string | null;
  estimated_revenue: string | null;
  maturity: string | null;
  deployment_evidence: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyDetail extends Company {
  problems: Problem[];
  sectors: Sector[];
  news: NewsArticle[];
}

export interface CompanyListResponse {
  items: Company[];
  total: number;
}
