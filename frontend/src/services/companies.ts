import { apiClient } from "@/api/client";
import type { Company, CompanyDetail, CompanyListResponse } from "@/types/company";

export async function getCompanies(): Promise<CompanyListResponse> {
  const response = await apiClient.get<CompanyListResponse>("/companies");
  return response.data;
}

export async function getCompanyById(companyId: string): Promise<CompanyDetail> {
  const response = await apiClient.get<CompanyDetail>(`/companies/${companyId}`);
  return response.data;
}
