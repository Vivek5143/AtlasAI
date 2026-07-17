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

export interface CompanyListResponse {
  items: Company[];
  total: number;
}
