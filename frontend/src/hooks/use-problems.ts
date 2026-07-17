import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getProblems, searchProblems } from "@/services/problems";
import type { Problem, ProblemListResponse } from "@/types/problem";

export const problemsQueryKey = ["problems"] as const;

export function useProblems(): {
  data: ProblemListResponse | undefined;
  isError: boolean;
  isLoading: boolean;
  problems: Problem[];
  refetch: () => Promise<unknown>;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  totalProblems: number;
} {
  const [searchTerm, setSearchTerm] = useState("");
  const normalizedSearchTerm = searchTerm.trim();

  const query = useQuery({
    queryKey: [...problemsQueryKey, normalizedSearchTerm],
    queryFn: () =>
      normalizedSearchTerm
        ? searchProblems(normalizedSearchTerm)
        : getProblems(),
  });

  return {
    data: query.data,
    isError: query.isError,
    isLoading: query.isLoading,
    problems: query.data?.items ?? [],
    refetch: async () => query.refetch(),
    searchTerm,
    setSearchTerm,
    totalProblems: query.data?.total ?? 0,
  };
}
