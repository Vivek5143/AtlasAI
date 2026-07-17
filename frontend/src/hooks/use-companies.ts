import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getCompanies } from "@/services/companies";
import type { Company, CompanyListResponse } from "@/types/company";

export const companiesQueryKey = ["companies"] as const;

export function useCompanies(): {
  companies: Company[];
  data: CompanyListResponse | undefined;
  isError: boolean;
  isLoading: boolean;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  refetch: () => Promise<unknown>;
  totalCompanies: number;
} {
  const [searchTerm, setSearchTerm] = useState("");
  const query = useQuery({
    queryKey: companiesQueryKey,
    queryFn: getCompanies,
  });

  const companies = useMemo(() => {
    const items = query.data?.items ?? [];
    const normalized = searchTerm.trim().toLowerCase();
    if (!normalized) {
      return items;
    }

    return items.filter((company) =>
      company.vendor_name.toLowerCase().includes(normalized),
    );
  }, [query.data?.items, searchTerm]);

  return {
    companies,
    data: query.data,
    isError: query.isError,
    isLoading: query.isLoading,
    searchTerm,
    setSearchTerm,
    refetch: async () => query.refetch(),
    totalCompanies: query.data?.total ?? 0,
  };
}
