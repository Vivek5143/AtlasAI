import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getSectors } from "@/services/sectors";
import type { Sector, SectorListResponse } from "@/types/sector";

export const sectorsQueryKey = ["sectors"] as const;

export function useSectors(): {
  data: SectorListResponse | undefined;
  isError: boolean;
  isLoading: boolean;
  refetch: () => Promise<unknown>;
  searchTerm: string;
  sectors: Sector[];
  setSearchTerm: (value: string) => void;
  totalSectors: number;
} {
  const [searchTerm, setSearchTerm] = useState("");
  const query = useQuery({
    queryKey: sectorsQueryKey,
    queryFn: getSectors,
  });

  const sectors = useMemo(() => {
    const items = query.data?.items ?? [];
    const normalized = searchTerm.trim().toLowerCase();
    if (!normalized) {
      return items;
    }

    return items.filter((sector) =>
      sector.name.toLowerCase().includes(normalized),
    );
  }, [query.data?.items, searchTerm]);

  return {
    data: query.data,
    isError: query.isError,
    isLoading: query.isLoading,
    refetch: async () => query.refetch(),
    searchTerm,
    sectors,
    setSearchTerm,
    totalSectors: query.data?.total ?? 0,
  };
}
