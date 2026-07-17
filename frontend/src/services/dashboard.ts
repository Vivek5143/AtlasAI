import { apiClient } from "@/api/client";
import type { DashboardResponse } from "@/types/dashboard";

export async function getDashboard(): Promise<DashboardResponse> {
  const response = await apiClient.get<DashboardResponse>("/dashboard");
  return response.data;
}
