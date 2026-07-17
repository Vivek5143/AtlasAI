import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getNews } from "@/services/news";
import type { NewsArticle, NewsListResponse } from "@/types/news";

export const newsQueryKey = ["news"] as const;

export function useNews(): {
  articles: NewsArticle[];
  data: NewsListResponse | undefined;
  isError: boolean;
  isLoading: boolean;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  refetch: () => Promise<unknown>;
  totalNews: number;
} {
  const [searchTerm, setSearchTerm] = useState("");
  const query = useQuery({
    queryKey: newsQueryKey,
    queryFn: getNews,
  });

  const articles = useMemo(() => {
    const items = query.data?.items ?? [];
    const normalized = searchTerm.trim().toLowerCase();
    if (!normalized) {
      return items;
    }

    return items.filter((article) =>
      article.title.toLowerCase().includes(normalized),
    );
  }, [query.data?.items, searchTerm]);

  return {
    articles,
    data: query.data,
    isError: query.isError,
    isLoading: query.isLoading,
    searchTerm,
    setSearchTerm,
    refetch: async () => query.refetch(),
    totalNews: query.data?.total ?? 0,
  };
}
