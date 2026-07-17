export interface Problem {
  external_problem_id: string | null;
  category: string | null;
  industry?: string | null;
  name: string;
  problem_type: string | null;
  vc_stage: string | null;
  severity: string | null;
  financial_impact: string | null;
  regulatory_trigger: string | null;
  ai_solution: string | null;
  id: string;
  created_at: string;
  updated_at: string;
}

export interface ProblemListResponse {
  items: Problem[];
  total: number;
}
