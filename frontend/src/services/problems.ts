import { apiClient } from "@/api/client";
import type { ProblemListResponse } from "@/types/problem";

export async function getProblems(): Promise<ProblemListResponse> {
  const response = await apiClient.get<ProblemListResponse>("/problems");
  return response.data;
}

export async function searchProblems(keyword: string): Promise<ProblemListResponse> {
  const response = await apiClient.get<ProblemListResponse>("/problems/search", {
    params: { keyword },
  });
  return response.data;
}
