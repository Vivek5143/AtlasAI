import { apiClient } from "@/api/client";
import type { CompanyListResponse } from "@/types/company";

export async function getCompanies(): Promise<CompanyListResponse> {
  const response = await apiClient.get<CompanyListResponse>("/companies");
  return response.data;
}
