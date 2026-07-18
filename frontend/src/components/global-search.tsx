import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Building2,
  Command,
  LoaderCircle,
  Newspaper,
  Search,
  Shapes,
  TriangleAlert,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { companiesQueryKey } from "@/hooks/use-companies";
import { newsQueryKey } from "@/hooks/use-news";
import { problemsQueryKey } from "@/hooks/use-problems";
import { sectorsQueryKey } from "@/hooks/use-sectors";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { cn } from "@/lib/utils";
import { getCompanies } from "@/services/companies";
import { getNews } from "@/services/news";
import { searchProblems } from "@/services/problems";
import { getSectors } from "@/services/sectors";

type SearchSource = "companies" | "problems" | "sectors" | "news";

type SearchResultItem = {
  id: string;
  meta: string;
  source: SearchSource;
  title: string;
  to: string;
};

type ResultGroup = {
  key: SearchSource;
  label: string;
  results: SearchResultItem[];
};

const MAX_RESULTS_PER_GROUP = 4;

function normalizeValue(value: string | null | undefined): string {
  return value?.trim().toLowerCase() ?? "";
}

function fieldMatches(
  query: string,
  values: Array<string | null | undefined>,
): boolean {
  return values.some((value) => normalizeValue(value).includes(query));
}

function formatArticleMeta(url: string, publishedAt: string): string {
  let source = "Unknown source";

  try {
    source = new URL(url).hostname.replace(/^www\./, "");
  } catch {
    source = "Unknown source";
  }

  const date = new Date(publishedAt);
  if (Number.isNaN(date.getTime())) {
    return source;
  }

  return `${source} / ${new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)}`;
}

function buildFilteredRoute(
  pathname: string,
  search: string,
  selected: string,
): string {
  const params = new URLSearchParams();
  params.set("search", search);
  params.set("selected", selected);
  return `${pathname}?${params.toString()}`;
}

function isTextInputTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    target.isContentEditable ||
    target.getAttribute("role") === "textbox"
  );
}

function SearchLoadingState(): ReactElement {
  return (
    <div className="space-y-4 px-4 py-5 sm:px-5">
      {Array.from({ length: 3 }).map((_, groupIndex) => (
        <div key={groupIndex} className="space-y-3">
          <div className="h-3 w-24 animate-pulse rounded-full bg-[#dde5dc] dark:bg-slate-800" />
          <div className="space-y-2">
            {Array.from({ length: 2 }).map((__, itemIndex) => (
              <div
                key={itemIndex}
                className="h-16 animate-pulse rounded-[1.5rem] bg-[#f1f4ee] dark:bg-slate-900"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SearchEmptyState({ query }: { query: string }): ReactElement {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="rounded-[1.75rem] border border-[#d7ddd1] bg-[#f6f5f0] px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
        <Search className="h-5 w-5 text-slate-500 dark:text-slate-400" aria-hidden="true" />
      </div>
      <h3 className="mt-5 font-editorial text-3xl tracking-[-0.04em] text-slate-950 dark:text-white">
        No results for &quot;{query}&quot;
      </h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
        Try a company name, problem keyword, sector, or news headline to broaden the search.
      </p>
    </div>
  );
}

function SearchIntroState(): ReactElement {
  return (
    <div className="flex flex-col gap-4 px-5 py-6">
      <div className="rounded-[1.75rem] border border-[#d7ddd1] bg-[linear-gradient(135deg,_rgba(255,255,255,0.98)_0%,_rgba(238,242,235,0.98)_100%)] p-5 shadow-sm dark:border-slate-800 dark:bg-[linear-gradient(135deg,_rgba(15,23,42,0.96)_0%,_rgba(2,6,23,0.96)_100%)]">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#2f6b51] dark:text-emerald-300">
          Global Search
        </p>
        <h3 className="mt-3 font-editorial text-3xl tracking-[-0.04em] text-slate-950 dark:text-white">
          Search across AtlasAI in one quiet workspace
        </h3>
        <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500 dark:text-slate-400">
          Type to search companies, problems, sectors, and news with grouped results and fast navigation.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {[
          "Companies by vendor, country, and AI category",
          "Problems by keyword using the existing search API",
          "Sectors by name from the current dataset",
          "News by headline and source context",
        ].map((hint) => (
          <div
            key={hint}
            className="rounded-2xl border border-[#d7ddd1] bg-white/90 px-4 py-3 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
          >
            {hint}
          </div>
        ))}
      </div>
    </div>
  );
}

function SearchResultRow({
  active,
  item,
  onHover,
  onSelect,
}: {
  active: boolean;
  item: SearchResultItem;
  onHover: () => void;
  onSelect: () => void;
}): ReactElement {
  const iconMap = {
    companies: Building2,
    problems: TriangleAlert,
    sectors: Shapes,
    news: Newspaper,
  } as const;

  const Icon = iconMap[item.source];

  return (
    <button
      type="button"
      onMouseEnter={onHover}
      onClick={onSelect}
      className={cn(
        "flex w-full items-center gap-4 rounded-[1.5rem] border px-4 py-3 text-left transition-all",
        active
          ? "border-[#bfd0c2] bg-[#edf4ee] shadow-sm dark:border-emerald-700/60 dark:bg-emerald-950/20"
          : "border-transparent bg-transparent hover:border-[#d8ddd4] hover:bg-[#f7f6f1] dark:hover:border-slate-800 dark:hover:bg-slate-950/70",
      )}
    >
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[#d7ddd1] bg-white text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
        <Icon className="h-4 w-4" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-slate-950 dark:text-white">{item.title}</p>
        <p className="mt-1 truncate text-sm text-slate-500 dark:text-slate-400">{item.meta}</p>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
    </button>
  );
}

export function GlobalSearch(): ReactElement {
  const navigate = useNavigate();
  const location = useLocation();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const debouncedSearchTerm = useDebouncedValue(searchTerm, 250);
  const normalizedDebouncedSearchTerm = normalizeValue(debouncedSearchTerm);
  const hasSearchTerm = normalizedDebouncedSearchTerm.length > 0;
  const isDebouncing =
    searchTerm.trim().length > 0 &&
    normalizeValue(searchTerm) !== normalizedDebouncedSearchTerm;

  const companiesQuery = useQuery({
    queryKey: companiesQueryKey,
    queryFn: getCompanies,
    enabled: isOpen && hasSearchTerm,
  });

  const problemsQuery = useQuery({
    queryKey: [...problemsQueryKey, normalizedDebouncedSearchTerm],
    queryFn: () => searchProblems(debouncedSearchTerm.trim()),
    enabled: isOpen && hasSearchTerm,
  });

  const sectorsQuery = useQuery({
    queryKey: sectorsQueryKey,
    queryFn: getSectors,
    enabled: isOpen && hasSearchTerm,
  });

  const newsQuery = useQuery({
    queryKey: newsQueryKey,
    queryFn: getNews,
    enabled: isOpen && hasSearchTerm,
  });

  const resultGroups = useMemo<ResultGroup[]>(() => {
    if (!hasSearchTerm) {
      return [];
    }

    const companies = (companiesQuery.data?.items ?? [])
      .filter((company) =>
        fieldMatches(normalizedDebouncedSearchTerm, [
          company.vendor_name,
          company.country,
          company.ai_category,
          company.company_type,
        ]),
      )
      .slice(0, MAX_RESULTS_PER_GROUP)
      .map((company) => ({
        id: `company-${company.id}`,
        meta: [company.country, company.ai_category].filter(Boolean).join(" / ") || "Company",
        source: "companies" as const,
        title: company.vendor_name,
        to: `/companies/${company.id}`,
      }));

    const problems = (problemsQuery.data?.items ?? [])
      .slice(0, MAX_RESULTS_PER_GROUP)
      .map((problem) => ({
        id: `problem-${problem.id}`,
        meta:
          [problem.category, problem.problem_type, problem.severity]
            .filter(Boolean)
            .join(" / ") || "Problem",
        source: "problems" as const,
        title: problem.name,
        to: buildFilteredRoute("/problems", problem.name, problem.id),
      }));

    const sectors = (sectorsQuery.data?.items ?? [])
      .filter((sector) => fieldMatches(normalizedDebouncedSearchTerm, [sector.name]))
      .slice(0, MAX_RESULTS_PER_GROUP)
      .map((sector) => ({
        id: `sector-${sector.id}`,
        meta: "Sector",
        source: "sectors" as const,
        title: sector.name,
        to: buildFilteredRoute("/sectors", sector.name, sector.id),
      }));

    const news = (newsQuery.data?.items ?? [])
      .filter((article) =>
        fieldMatches(normalizedDebouncedSearchTerm, [article.title, article.url]),
      )
      .slice(0, MAX_RESULTS_PER_GROUP)
      .map((article) => ({
        id: `news-${article.id}`,
        meta: formatArticleMeta(article.url, article.published_at),
        source: "news" as const,
        title: article.title,
        to: buildFilteredRoute("/news", article.title, article.id),
      }));

    return [
      { key: "companies", label: "Companies", results: companies },
      { key: "problems", label: "Problems", results: problems },
      { key: "sectors", label: "Sectors", results: sectors },
      { key: "news", label: "News", results: news },
    ];
  }, [
    companiesQuery.data?.items,
    debouncedSearchTerm,
    hasSearchTerm,
    newsQuery.data?.items,
    normalizedDebouncedSearchTerm,
    problemsQuery.data?.items,
    sectorsQuery.data?.items,
  ]);

  const flattenedResults = useMemo(
    () => resultGroups.flatMap((group) => group.results),
    [resultGroups],
  );

  const hasAnyResults = flattenedResults.length > 0;
  const allQueriesFailed =
    companiesQuery.isError &&
    problemsQuery.isError &&
    sectorsQuery.isError &&
    newsQuery.isError;

  const isLoadingResults =
    hasSearchTerm &&
    (isDebouncing ||
      companiesQuery.isLoading ||
      problemsQuery.isLoading ||
      sectorsQuery.isLoading ||
      newsQuery.isLoading);

  const isRefreshingResults =
    hasSearchTerm &&
    !isLoadingResults &&
    (companiesQuery.isFetching ||
      problemsQuery.isFetching ||
      sectorsQuery.isFetching ||
      newsQuery.isFetching);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      inputRef.current?.focus();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    setIsOpen(false);
    setSearchTerm("");
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent): void => {
      const isOpenShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      const isSlashShortcut =
        event.key === "/" &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey &&
        !isTextInputTarget(event.target);

      if (isOpenShortcut || isSlashShortcut) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      const isOpenShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      const isSlashShortcut =
        event.key === "/" &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey &&
        !isTextInputTarget(event.target);

      if (isOpenShortcut || isSlashShortcut) {
        event.preventDefault();
        setIsOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!flattenedResults.length) {
      setActiveIndex(-1);
      return;
    }

    setActiveIndex(0);
  }, [flattenedResults.length, normalizedDebouncedSearchTerm]);

  const handleSelectResult = (item: SearchResultItem): void => {
    navigate(item.to);
  };

  const handleInputKeyDown = (event: ReactKeyboardEvent<HTMLInputElement>): void => {
    if (event.key === "Escape") {
      event.preventDefault();
      setIsOpen(false);
      return;
    }

    if (event.key === "ArrowDown" && flattenedResults.length > 0) {
      event.preventDefault();
      setActiveIndex((current) => Math.min(current + 1, flattenedResults.length - 1));
      return;
    }

    if (event.key === "ArrowUp" && flattenedResults.length > 0) {
      event.preventDefault();
      setActiveIndex((current) => Math.max(current - 1, 0));
      return;
    }

    if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      handleSelectResult(flattenedResults[activeIndex]);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="hidden h-11 min-w-[18rem] items-center justify-between gap-3 rounded-full border border-[#d7ddd1] bg-white/90 px-4 text-sm text-slate-500 shadow-sm transition-colors hover:border-[#bcc9bf] hover:bg-white md:inline-flex dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-400 dark:hover:border-slate-700"
      >
        <span className="flex items-center gap-2">
          <Search className="h-4 w-4" aria-hidden="true" />
          <span>Search AtlasAI</span>
        </span>
        <span className="inline-flex items-center gap-1 rounded-full border border-[#d7ddd1] bg-[#f6f5f0] px-2.5 py-1 text-xs font-medium text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400">
          <Command className="h-3.5 w-3.5" aria-hidden="true" />
          <span>K</span>
        </span>
      </button>

      <button
        type="button"
        aria-label="Open global search"
        onClick={() => setIsOpen(true)}
        className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-[#d7ddd1] bg-white/90 text-slate-600 shadow-sm transition-colors hover:bg-white hover:text-slate-950 md:hidden dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
      >
        <Search className="h-4 w-4" aria-hidden="true" />
      </button>

      {isOpen ? (
        <div
          className="fixed inset-0 z-[70] bg-slate-950/45 px-3 py-4 backdrop-blur-md sm:px-6"
          role="dialog"
          aria-modal="true"
          aria-label="Global search"
          onClick={() => setIsOpen(false)}
        >
          <div
            className="mx-auto flex max-h-[calc(100vh-2rem)] w-full max-w-3xl flex-col overflow-hidden rounded-[2rem] border border-[#d7ddd1] bg-[#fbfaf6]/95 shadow-[0_40px_120px_-40px_rgba(15,23,42,0.45)] dark:border-slate-800/80 dark:bg-slate-950/95"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="border-b border-[#d7ddd1] px-4 py-4 dark:border-slate-800 sm:px-5">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[#d7ddd1] bg-[#f6f5f0] text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
                  {isRefreshingResults || isLoadingResults ? (
                    <LoaderCircle className="h-5 w-5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Search className="h-5 w-5" aria-hidden="true" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <label htmlFor="global-search-input" className="sr-only">
                    Search AtlasAI
                  </label>
                  <input
                    id="global-search-input"
                    ref={inputRef}
                    type="search"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    onKeyDown={handleInputKeyDown}
                    placeholder="Search companies, problems, sectors, and news"
                    className="h-11 w-full bg-transparent text-base text-slate-950 outline-none placeholder:text-slate-400 dark:text-white dark:placeholder:text-slate-500"
                  />
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span>Grouped results</span>
                    <span className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-700" />
                    <span>Enter to open</span>
                    <span className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-700" />
                    <span>Esc to close</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="min-h-[22rem] flex-1 overflow-y-auto">
              {!searchTerm.trim() ? (
                <SearchIntroState />
              ) : isLoadingResults && !hasAnyResults ? (
                <SearchLoadingState />
              ) : allQueriesFailed ? (
                <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
                  <div className="rounded-3xl border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900/50 dark:bg-red-950/20">
                    <TriangleAlert
                      className="h-5 w-5 text-red-600 dark:text-red-300"
                      aria-hidden="true"
                    />
                  </div>
                  <h3 className="mt-5 font-editorial text-3xl tracking-[-0.04em] text-slate-950 dark:text-white">
                    Search is temporarily unavailable
                  </h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
                    AtlasAI could not load search data from the current APIs. Please try again.
                  </p>
                </div>
              ) : !hasAnyResults ? (
                <SearchEmptyState query={searchTerm.trim()} />
              ) : (
                <div className="space-y-5 px-4 py-5 sm:px-5">
                  {resultGroups.map((group) =>
                    group.results.length > 0 ? (
                      <section key={group.key} className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
                            {group.label}
                          </h3>
                          <span className="text-xs text-slate-400 dark:text-slate-500">
                            {group.results.length} result{group.results.length === 1 ? "" : "s"}
                          </span>
                        </div>
                        <div className="space-y-2">
                          {group.results.map((item) => {
                            const itemIndex = flattenedResults.findIndex(
                              (entry) => entry.id === item.id,
                            );

                            return (
                              <SearchResultRow
                                key={item.id}
                                active={itemIndex === activeIndex}
                                item={item}
                                onHover={() => setActiveIndex(itemIndex)}
                                onSelect={() => handleSelectResult(item)}
                              />
                            );
                          })}
                        </div>
                      </section>
                    ) : null,
                  )}
                </div>
              )}
            </div>

            <div className="border-t border-[#d7ddd1] px-4 py-3 dark:border-slate-800 sm:px-5">
              <div className="flex flex-col gap-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between dark:text-slate-400">
                <span>Search spans the existing AtlasAI companies, problems, sectors, and news APIs.</span>
                <span className="inline-flex items-center gap-2">
                  <kbd className="rounded-md border border-[#d7ddd1] bg-[#f6f5f0] px-2 py-1 font-medium dark:border-slate-700 dark:bg-slate-900">
                    Ctrl
                  </kbd>
                  <span>+</span>
                  <kbd className="rounded-md border border-[#d7ddd1] bg-[#f6f5f0] px-2 py-1 font-medium dark:border-slate-700 dark:bg-slate-900">
                    K
                  </kbd>
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
