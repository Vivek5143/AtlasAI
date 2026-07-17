import { apiClient } from "@/api/client";
import type { NewsListResponse } from "@/types/news";

export async function getNews(): Promise<NewsListResponse> {
  const response = await apiClient.get<NewsListResponse>("/news");
  return response.data;
}

export async function getCompanyNews(
  companyId: string,
): Promise<NewsListResponse> {
  const response = await apiClient.get<NewsListResponse>(
    `/news/company/${companyId}`,
  );
  return response.data;
}
