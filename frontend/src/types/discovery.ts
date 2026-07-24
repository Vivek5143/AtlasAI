import type { Company } from "@/types/company";

export type CompanyDiscoveryCandidate = {
  id: string;
  company_name: string;
  normalized_name: string;
  website: string | null;
  website_domain: string | null;
  country: string | null;
  description: string | null;
  ai_category: string | null;
  provider?: string;
  provider_company_id?: string | null;
  provider_metadata?: Record<string, any> | null;
  evidence_url: string;
  evidence_title: string | null;
  evidence_text: string | null;
  source_domain: string | null;
  confidence_score: number;
  confidence_reasons: string[];
  status: string;
  rejection_reason: string | null;
  approved_company_id: string | null;
  discovered_at: string;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyDiscoverySearchRequest = {
  query?: string | null;
  sector?: string | null;
  country?: string | null;
  limit: number;
};

export type CompanyDiscoverySkippedCandidate = {
  company_name: string | null;
  evidence_url: string | null;
  reason: string;
};

export type CompanyDiscoveryProviderExtractionDetail = {
  title: string | null;
  source_domain: string | null;
  extraction_skip_reason: string;
};

export type CompanyDiscoverySearchResponse = {
  candidates_found: number;
  candidates_created: number;
  candidates_skipped: number;
  articles_fetched: number;
  provider_candidates_extracted: number;
  provider_extraction_skipped: number;
  items: CompanyDiscoveryCandidate[];
  skipped: CompanyDiscoverySkippedCandidate[];
  provider_extraction_details: CompanyDiscoveryProviderExtractionDetail[];
};

export type CompanyDiscoveryListResponse = {
  items: CompanyDiscoveryCandidate[];
  total: number;
};

export type CompanyDiscoveryApprovalResponse = {
  company: Company;
  indexing_status: string;
  indexed_chunks: number;
};
