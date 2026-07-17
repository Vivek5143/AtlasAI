import type { AxiosError } from "axios";
import { useQuery } from "@tanstack/react-query";

import { getCompanyById } from "@/services/companies";
import type { CompanyDetail } from "@/types/company";

type ApiError = AxiosError<{ detail?: string }>;

export const companyDetailQueryKey = (companyId: string) =>
  ["company", companyId] as const;

export function useCompanyDetail(companyId: string | undefined): {
  company: CompanyDetail | null;
  companyError: ApiError | null;
  companyNotFound: boolean;
  companyLoading: boolean;
  refetchCompany: () => Promise<unknown>;
} {
  const companyQuery = useQuery<CompanyDetail, ApiError>({
    queryKey: companyId ? companyDetailQueryKey(companyId) : ["company", "missing"],
    queryFn: () => getCompanyById(companyId ?? ""),
    enabled: Boolean(companyId),
    retry: false,
  });

  return {
    company: companyQuery.data ?? null,
    companyError: companyQuery.error ?? null,
    companyNotFound: companyQuery.error?.response?.status === 404,
    companyLoading: companyQuery.isLoading,
    refetchCompany: async () => companyQuery.refetch(),
  };
}
