export interface Metadata {
  id?: string | null;
  entity_type?: string | null;
  title?: string | null;
  created_at?: string | null;
  company_id?: string | null;
  problem_id?: string | null;
  news_id?: string | null;
  sector_id?: string | null;
  source?: string | null;
  chunk_index?: number | null;
  score?: number | null;
}

export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
  sources: string[];
  metadata: Metadata[];
}

export interface Source {
  id: string;
  label: string;
  title: string;
  href?: string;
  entityType?: string | null;
  companyId?: string | null;
}

export type ChatRole = "assistant" | "user";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  sources: Source[];
  metadata: Metadata[];
}
