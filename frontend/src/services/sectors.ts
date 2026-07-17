import { apiClient } from "@/api/client";
import type { SectorListResponse } from "@/types/sector";

export async function getSectors(): Promise<SectorListResponse> {
  const response = await apiClient.get<SectorListResponse>("/sectors");
  return response.data;
}
