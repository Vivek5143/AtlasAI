import { useEffect, useMemo, useState } from "react";
import type { ReactElement } from "react";
import { Filter, Link2, RefreshCcw, Search, X } from "lucide-react";
import { useSearchParams } from "react-router-dom";

import { PageContainer } from "@/components/page-container";
import { useNews } from "@/hooks/use-news";
import type { NewsArticle } from "@/types/news";

function extractSource(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return "Unknown source";
  }
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}

function fieldLabel(key: keyof NewsArticle): string {
  if (key === "company_id") {
    return "Company ID";
  }
  if (key === "published_at") {
    return "Published At";
  }
  if (key === "created_at") {
    return "Created At";
  }
  if (key === "updated_at") {
    return "Updated At";
  }
  return key.charAt(0).toUpperCase() + key.slice(1);
}

function fieldValue(key: keyof NewsArticle, value: NewsArticle[keyof NewsArticle]): string {
  if (!value) {
    return "—";
  }

  if (key === "published_at" || key === "created_at" || key === "updated_at") {
    return formatDate(String(value));
  }

  return String(value);
}

function NewsSkeletonCard(): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-4 h-3 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-5 h-3 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-3 w-5/6 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    </article>
  );
}

function NewsDetailsDrawer({
  article,
  onClose,
}: {
  article: NewsArticle;
  onClose: () => void;
}): ReactElement {
  const entries = Object.entries(article) as [
    keyof NewsArticle,
    NewsArticle[keyof NewsArticle],
  ][];

  return (
    <div
      className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm"
      role="presentation"
      onClick={onClose}
    >
      <aside
        className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-950 sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-label="News article details"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              News article
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950 dark:text-white">
              {article.title}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close news details"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {entries.map(([key, value]) => (
            <article
              key={key}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {fieldLabel(key)}
              </p>
              {key === "url" && typeof value === "string" ? (
                <a
                  href={value}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 block break-all text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  {value}
                </a>
              ) : (
                <p className="mt-2 break-words text-sm text-slate-800 dark:text-slate-200">
                  {fieldValue(key, value)}
                </p>
              )}
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

export function NewsPage(): ReactElement {
  const {
    articles,
    isError,
    isLoading,
    refetch,
    searchTerm,
    setSearchTerm,
    totalNews,
  } = useNews();
  const [searchParams] = useSearchParams();
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [consumedSelectedArticleId, setConsumedSelectedArticleId] = useState<string | null>(
    null,
  );

  const routedSearchTerm = searchParams.get("search") ?? "";
  const routedSelectedArticleId = searchParams.get("selected");

  useEffect(() => {
    setSearchTerm(routedSearchTerm);
  }, [routedSearchTerm, setSearchTerm]);

  useEffect(() => {
    setConsumedSelectedArticleId(null);
  }, [routedSelectedArticleId]);

  const articleCards = useMemo(
    () =>
      articles.map((article) => {
        const source = extractSource(article.url);
        const publishedAt = formatDate(article.published_at);

        return (
          <article
            key={article.id}
            onClick={() => setSelectedArticle(article)}
            className="cursor-pointer rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-800/80"
          >
            <h2 className="line-clamp-2 text-base font-semibold text-slate-950 dark:text-white">
              {article.title}
            </h2>
            <div className="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
              <p>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  Company:
                </span>{" "}
                {article.company_id || "—"}
              </p>
              <p>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  Published:
                </span>{" "}
                {publishedAt}
              </p>
              <p>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  Source:
                </span>{" "}
                {source}
              </p>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
              This record is available from the backend and can be reviewed in
              detail.
            </p>
            <a
              href={article.url}
              target="_blank"
              rel="noreferrer"
              onClick={(event) => event.stopPropagation()}
              className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              <Link2 className="h-4 w-4" aria-hidden="true" />
              Open source
            </a>
          </article>
        );
      }),
    [articles],
  );

  useEffect(() => {
    if (!selectedArticle) {
      return;
    }

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setSelectedArticle(null);
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [selectedArticle]);

  useEffect(() => {
    if (!routedSelectedArticleId || consumedSelectedArticleId === routedSelectedArticleId) {
      return;
    }

    const matchingArticle =
      articles.find((article) => article.id === routedSelectedArticleId) ?? null;

    if (!matchingArticle) {
      return;
    }

    setSelectedArticle(matchingArticle);
    setConsumedSelectedArticleId(routedSelectedArticleId);
  }, [articles, consumedSelectedArticleId, routedSelectedArticleId]);

  return (
    <PageContainer
      title="News"
      subtitle="Track persisted company-related news articles from the AtlasAI backend."
    >
      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="relative w-full lg:max-w-md">
            <span className="sr-only">Search news by title</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by headline/title"
              className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500"
            />
          </label>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              News Count: {totalNews.toLocaleString()}
            </span>
            <button
              type="button"
              onClick={() => {
                void refetch();
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </button>
            <button
              type="button"
              disabled
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-400 dark:border-slate-800 dark:text-slate-500"
            >
              <Filter className="h-4 w-4" aria-hidden="true" />
              Filter
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <NewsSkeletonCard key={index} />
            ))}
          </div>
        ) : null}

        {!isLoading && isError ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-5 dark:border-red-900/60 dark:bg-red-950/30">
            <h2 className="text-base font-semibold text-red-700 dark:text-red-300">
              Unable to load news
            </h2>
            <p className="mt-2 text-sm text-red-600 dark:text-red-200/80">
              We could not fetch the latest news articles. Please try again.
            </p>
            <button
              type="button"
              onClick={() => {
                void refetch();
              }}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
            >
              <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              Retry
            </button>
          </section>
        ) : null}

        {!isLoading && !isError && articles.length === 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">
              {searchTerm.trim() ? "No matching articles" : "No news available"}
            </h2>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {searchTerm.trim()
                ? "Try another keyword to broaden your search."
                : "The backend returned an empty news feed."}
            </p>
          </section>
        ) : null}

        {!isLoading && !isError && articles.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{articleCards}</div>
        ) : null}
      </section>

      {selectedArticle ? (
        <NewsDetailsDrawer
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      ) : null}
    </PageContainer>
  );
}
