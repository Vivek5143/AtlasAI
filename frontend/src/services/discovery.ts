import { apiClient } from "@/api/client";
import type {
  CompanyDiscoveryApprovalResponse,
  CompanyDiscoveryCandidate,
  CompanyDiscoveryListResponse,
  CompanyDiscoverySearchRequest,
  CompanyDiscoverySearchResponse,
} from "@/types/discovery";

export async function searchDiscoveryCandidates(
  payload: CompanyDiscoverySearchRequest,
): Promise<CompanyDiscoverySearchResponse> {
  const response = await apiClient.post<CompanyDiscoverySearchResponse>(
    "/discovery/search",
    payload,
  );
  return response.data;
}

export async function getPendingDiscoveryCandidates(
  limit = 50,
): Promise<CompanyDiscoveryListResponse> {
  const response = await apiClient.get<CompanyDiscoveryListResponse>(
    "/discovery/pending",
    { params: { limit } },
  );
  return response.data;
}

export async function getDiscoveryCandidate(
  candidateId: string,
): Promise<CompanyDiscoveryCandidate> {
  const response = await apiClient.get<CompanyDiscoveryCandidate>(
    `/discovery/${candidateId}`,
  );
  return response.data;
}

export async function approveDiscoveryCandidate(
  candidateId: string,
): Promise<CompanyDiscoveryApprovalResponse> {
  const response = await apiClient.post<CompanyDiscoveryApprovalResponse>(
    `/discovery/${candidateId}/approve`,
  );
  return response.data;
}

export async function rejectDiscoveryCandidate(
  candidateId: string,
  rejectionReason: string,
): Promise<CompanyDiscoveryCandidate> {
  const response = await apiClient.post<CompanyDiscoveryCandidate>(
    `/discovery/${candidateId}/reject`,
    { rejection_reason: rejectionReason },
  );
  return response.data;
}
