import { useQuery } from "@tanstack/react-query";

import { getDashboard } from "@/services/dashboard";
import type { DashboardMetrics, DashboardResponse } from "@/types/dashboard";

export const dashboardQueryKey = ["dashboard"] as const;

export function useDashboard(): {
  dashboard: DashboardMetrics | null;
  data: DashboardResponse | undefined;
  isError: boolean;
  isLoading: boolean;
  refetch: () => Promise<unknown>;
} {
  const query = useQuery({
    queryKey: dashboardQueryKey,
    queryFn: getDashboard,
  });

  return {
    dashboard: query.data?.items[0] ?? null,
    data: query.data,
    isError: query.isError,
    isLoading: query.isLoading,
    refetch: async () => query.refetch(),
  };
}
