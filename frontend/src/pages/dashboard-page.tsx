import type { ReactElement, ReactNode } from "react";
import { Children, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Bot,
  Building2,
  Layers3,
  Newspaper,
  RefreshCcw,
  TriangleAlert,
} from "lucide-react";
import { Link } from "react-router-dom";

import {
  ChartSkeletonCard,
  CompaniesByAICategoryChart,
  CompaniesByCountryChart,
  DatasetCoverageChart,
  NewsPublishedTimelineChart,
  ProblemsBySeverityChart,
  WidgetEmpty,
  WidgetError,
  type ChartDatum,
} from "@/components/dashboard-charts";
import { companiesQueryKey, useCompanies } from "@/hooks/use-companies";
import { dashboardQueryKey, useDashboard } from "@/hooks/use-dashboard";
import { newsQueryKey, useNews } from "@/hooks/use-news";
import { problemsQueryKey, useProblems } from "@/hooks/use-problems";
import { sectorsQueryKey, useSectors } from "@/hooks/use-sectors";
import type { Company } from "@/types/company";
import type { NewsArticle } from "@/types/news";

type MetricCardProps = {
  description: string;
  icon: ReactElement;
  isLoading: boolean;
  label: string;
  status?: string;
  value: number;
};

type RecentSectionProps = {
  children: ReactNode;
  emptyMessage: string;
  isError: boolean;
  isLoading: boolean;
  title: string;
  to: string;
};

type RecentCompany = Pick<
  Company,
  "ai_category" | "country" | "created_at" | "id" | "vendor_name"
>;

type RecentArticle = Pick<
  NewsArticle,
  "id" | "published_at" | "title" | "url"
>;

function normalizeLabel(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function safeDateValue(value: string): number {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function aggregateByLabel<T>(
  items: T[],
  selector: (item: T) => string | null | undefined,
  options?: {
    emptyLabel?: string;
    includeEmpty?: boolean;
    limit?: number;
  },
): ChartDatum[] {
  const counts = new Map<string, number>();
  const emptyLabel = options?.emptyLabel ?? "Unspecified";
  const includeEmpty = options?.includeEmpty ?? true;
  const limit = options?.limit;

  for (const item of items) {
    const label = normalizeLabel(selector(item));
    if (!label && !includeEmpty) {
      continue;
    }

    const resolvedLabel = label ?? emptyLabel;
    counts.set(resolvedLabel, (counts.get(resolvedLabel) ?? 0) + 1);
  }

  const sorted = [...counts.entries()].sort(
    ([labelA, valueA], [labelB, valueB]) => valueB - valueA || labelA.localeCompare(labelB),
  );

  if (!limit || sorted.length <= limit) {
    return sorted.map(([label, value]) => ({ label, value }));
  }

  const visible = sorted.slice(0, limit);
  const remainingTotal = sorted.slice(limit).reduce((total, [, value]) => total + value, 0);

  return remainingTotal > 0
    ? [...visible.map(([label, value]) => ({ label, value })), { label: "Other", value: remainingTotal }]
    : visible.map(([label, value]) => ({ label, value }));
}

function formatTimelineLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
  }).format(date);
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatArticleSource(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "Unknown source";
  }
}

function buildFilteredRoute(pathname: string, search: string, selected: string): string {
  const params = new URLSearchParams();
  params.set("search", search);
  params.set("selected", selected);
  return `${pathname}?${params.toString()}`;
}

function sortLatest<T>(items: T[], dateSelector: (item: T) => string): T[] {
  return [...items].sort(
    (a, b) => safeDateValue(dateSelector(b)) - safeDateValue(dateSelector(a)),
  );
}

function LoadingSkeletonCard(): ReactElement {
  return (
    <div className="rounded-[1.9rem] border border-[#d7ddd1] bg-[#fcfaf6] p-5 shadow-[0_24px_60px_-42px_rgba(15,23,42,0.38)] dark:border-slate-800 dark:bg-slate-900">
      <div className="h-4 w-28 animate-pulse rounded bg-[#dde5dc] dark:bg-slate-800" />
      <div className="mt-4 h-10 w-20 animate-pulse rounded bg-[#e6ece4] dark:bg-slate-800" />
      <div className="mt-3 h-4 w-full animate-pulse rounded bg-[#eef2ea] dark:bg-slate-800" />
      <div className="mt-2 h-4 w-4/5 animate-pulse rounded bg-[#eef2ea] dark:bg-slate-800" />
    </div>
  );
}

function MetricCard({
  description,
  icon,
  isLoading,
  label,
  status,
  value,
}: MetricCardProps): ReactElement {
  if (isLoading) {
    return <LoadingSkeletonCard />;
  }

  return (
    <article className="overflow-hidden rounded-[1.9rem] border border-[#d7ddd1] bg-[#fcfaf6] p-5 shadow-[0_24px_60px_-42px_rgba(15,23,42,0.38)] dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-3 font-editorial text-5xl tracking-[-0.05em] text-slate-950 dark:text-white">
            {value.toLocaleString()}
          </p>
          {status ? (
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#2f6b51] dark:text-emerald-300">
              {status}
            </p>
          ) : null}
        </div>
        <div className="rounded-[1.4rem] border border-[#d7ddd1] bg-white/85 p-3 text-[#214938] dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
          {icon}
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
    </article>
  );
}

function RecentSection({
  children,
  emptyMessage,
  isError,
  isLoading,
  title,
  to,
}: RecentSectionProps): ReactElement {
  return (
    <article className="rounded-[1.9rem] border border-[#d7ddd1] bg-[#fcfaf6] p-5 shadow-[0_24px_60px_-42px_rgba(15,23,42,0.38)] dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
            Recent Data
          </p>
          <h3 className="mt-2 font-editorial text-3xl tracking-[-0.04em] text-slate-950 dark:text-white">
            {title}
          </h3>
        </div>
        <Link
          to={to}
          className="inline-flex items-center gap-2 rounded-full border border-[#d7ddd1] bg-white px-3 py-2 text-sm font-medium text-[#214938] transition-colors hover:bg-[#edf4ee] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
        >
          <span>View all</span>
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>

      {isLoading ? (
        <div className="mt-5 space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-20 animate-pulse rounded-[1.5rem] bg-[#eef2ea] dark:bg-slate-800"
            />
          ))}
        </div>
      ) : isError ? (
        <div className="mt-5">
          <WidgetError
            title={`${title} unavailable`}
            message="The dataset could not be loaded right now."
          />
        </div>
      ) : Children.count(children) > 0 ? (
        <div className="mt-5 space-y-3">{children}</div>
      ) : (
        <div className="mt-5">
          <WidgetEmpty title="No records available" message={emptyMessage} />
        </div>
      )}
    </article>
  );
}

export function DashboardPage(): ReactElement {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const dashboardQuery = useDashboard();
  const companiesQuery = useCompanies();
  const problemsQuery = useProblems();
  const newsQuery = useNews();
  const sectorsQuery = useSectors();

  const metricCards = useMemo(
    () => [
      {
        label: "Total Companies",
        value: dashboardQuery.dashboard?.total_companies ?? companiesQuery.totalCompanies,
        isLoading: !dashboardQuery.dashboard && companiesQuery.isLoading,
        description: "Tracked AI companies currently available inside AtlasAI.",
        status: companiesQuery.isError ? "Company feed unavailable" : "Live company dataset",
        icon: <Building2 className="h-5 w-5" aria-hidden="true" />,
      },
      {
        label: "Total Problems",
        value: dashboardQuery.dashboard?.total_problems ?? problemsQuery.totalProblems,
        isLoading: !dashboardQuery.dashboard && problemsQuery.isLoading,
        description: "Problem records ready for analysis, severity review, and mapping.",
        status: problemsQuery.isError ? "Problem feed unavailable" : "Live problem dataset",
        icon: <TriangleAlert className="h-5 w-5" aria-hidden="true" />,
      },
      {
        label: "Total Sectors",
        value: dashboardQuery.dashboard?.total_sectors ?? sectorsQuery.totalSectors,
        isLoading: !dashboardQuery.dashboard && sectorsQuery.isLoading,
        description: "Sector records available for grouping and market discovery.",
        status: sectorsQuery.isError ? "Sector feed unavailable" : "Live sector dataset",
        icon: <Layers3 className="h-5 w-5" aria-hidden="true" />,
      },
      {
        label: "Total News",
        value: dashboardQuery.dashboard?.total_news_articles ?? newsQuery.totalNews,
        isLoading: !dashboardQuery.dashboard && newsQuery.isLoading,
        description: "News articles linked to companies and market developments.",
        status: newsQuery.isError ? "News feed unavailable" : "Live news dataset",
        icon: <Newspaper className="h-5 w-5" aria-hidden="true" />,
      },
    ],
    [
      companiesQuery.isError,
      companiesQuery.isLoading,
      companiesQuery.totalCompanies,
      dashboardQuery.dashboard,
      newsQuery.isError,
      newsQuery.isLoading,
      newsQuery.totalNews,
      problemsQuery.isError,
      problemsQuery.isLoading,
      problemsQuery.totalProblems,
      sectorsQuery.isError,
      sectorsQuery.isLoading,
      sectorsQuery.totalSectors,
    ],
  );

  const companiesByCountryData = useMemo(
    () =>
      aggregateByLabel(companiesQuery.companies, (company) => company.country, {
        emptyLabel: "Unknown Country",
        limit: 7,
      }),
    [companiesQuery.companies],
  );

  const companiesByAICategoryData = useMemo(
    () =>
      aggregateByLabel(companiesQuery.companies, (company) => company.ai_category, {
        emptyLabel: "Unspecified Category",
        limit: 6,
      }),
    [companiesQuery.companies],
  );

  const hasProblemSeverityData = useMemo(
    () => problemsQuery.problems.some((problem) => Boolean(normalizeLabel(problem.severity))),
    [problemsQuery.problems],
  );

  const problemsBySeverityData = useMemo(
    () =>
      aggregateByLabel(problemsQuery.problems, (problem) => problem.severity, {
        includeEmpty: false,
        limit: 7,
      }),
    [problemsQuery.problems],
  );

  const newsTimelineData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();

    for (const article of newsQuery.articles) {
      const date = new Date(article.published_at);
      if (Number.isNaN(date.getTime())) {
        continue;
      }

      const isoDate = date.toISOString().slice(0, 10);
      counts.set(isoDate, (counts.get(isoDate) ?? 0) + 1);
    }

    return [...counts.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-10)
      .map(([label, value]) => ({
        label: formatTimelineLabel(label),
        value,
      }));
  }, [newsQuery.articles]);

  const coverageData = useMemo<ChartDatum[]>(() => {
    const dashboard = dashboardQuery.dashboard;
    if (!dashboard) {
      return [];
    }

    const coverageRows = [
      {
        label: "Companies with sectors",
        numerator: dashboard.companies_with_sectors,
        denominator: dashboard.total_companies,
      },
      {
        label: "Companies with news",
        numerator: dashboard.companies_with_news,
        denominator: dashboard.total_companies,
      },
      {
        label: "Sectors with companies",
        numerator: dashboard.sectors_with_companies,
        denominator: dashboard.total_sectors,
      },
      {
        label: "Problems with category",
        numerator: dashboard.problems_with_category,
        denominator: dashboard.total_problems,
      },
      {
        label: "Problems with severity",
        numerator: dashboard.problems_with_severity,
        denominator: dashboard.total_problems,
      },
    ];

    return coverageRows
      .filter((item) => item.denominator > 0)
      .map((item) => ({
        label: item.label,
        value: Math.round((item.numerator / item.denominator) * 100),
        detail: `${item.numerator.toLocaleString()} of ${item.denominator.toLocaleString()} records`,
      }));
  }, [dashboardQuery.dashboard]);

  const recentCompanies = useMemo(
    () =>
      sortLatest<RecentCompany>(companiesQuery.companies, (company) => company.created_at).slice(0, 5),
    [companiesQuery.companies],
  );

  const latestNews = useMemo(
    () => sortLatest<RecentArticle>(newsQuery.articles, (article) => article.published_at).slice(0, 5),
    [newsQuery.articles],
  );

  const handleRefreshDashboard = async (): Promise<void> => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: dashboardQueryKey }),
        queryClient.invalidateQueries({ queryKey: companiesQueryKey }),
        queryClient.invalidateQueries({ queryKey: problemsQueryKey }),
        queryClient.invalidateQueries({ queryKey: sectorsQueryKey }),
        queryClient.invalidateQueries({ queryKey: newsQueryKey }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <section className="mx-auto flex w-full max-w-[92rem] flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-[2.2rem] border border-[#d7ddd1] bg-[linear-gradient(135deg,_rgba(255,255,255,0.9)_0%,_rgba(238,242,235,0.92)_55%,_rgba(228,235,227,0.96)_100%)] p-6 shadow-[0_32px_80px_-52px_rgba(15,23,42,0.4)] dark:border-slate-800 dark:bg-[linear-gradient(135deg,_rgba(15,23,42,0.96)_0%,_rgba(3,7,18,0.98)_100%)] sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,0.85fr)]">
          <div className="relative overflow-hidden rounded-[1.8rem] border border-white/60 bg-white/70 p-6 dark:border-slate-800 dark:bg-slate-950/50">
            <div className="pointer-events-none absolute inset-y-0 right-0 w-56 bg-[radial-gradient(circle_at_right,_rgba(33,73,56,0.14),_transparent_62%)] dark:bg-[radial-gradient(circle_at_right,_rgba(52,211,153,0.12),_transparent_62%)]" />
            <p className="relative text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#2f6b51] dark:text-emerald-300">
              AtlasAI Intelligence Overview
            </p>
            <h2 className="relative mt-4 max-w-3xl font-editorial text-4xl tracking-[-0.06em] text-slate-950 dark:text-white sm:text-5xl">
              Understand where AI is transforming industries.
            </h2>
            <p className="relative mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-base">
              AtlasAI summarizes the live dataset across AI companies, market problems, sectors,
              news coverage, and AI-powered research through Ask AtlasAI.
            </p>
            <div className="relative mt-6 flex flex-wrap gap-3">
              <Link
                to="/ask"
                className="inline-flex items-center gap-2 rounded-full bg-[#214938] px-5 py-3 text-sm font-medium text-[#f6f2e8] shadow-[0_20px_40px_-28px_rgba(28,71,54,0.7)] transition-transform hover:scale-[1.01] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
              >
                <Bot className="h-4 w-4" aria-hidden="true" />
                <span>Ask AtlasAI</span>
              </Link>
              <Link
                to="/companies"
                className="inline-flex items-center gap-2 rounded-full border border-[#cfd8d1] bg-white px-5 py-3 text-sm font-medium text-[#214938] transition-colors hover:bg-[#edf4ee] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900"
              >
                <span>Explore Companies</span>
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <button
                type="button"
                onClick={() => {
                  void handleRefreshDashboard();
                }}
                className="inline-flex items-center gap-2 rounded-full border border-[#cfd8d1] bg-transparent px-5 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-white/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
              >
                <RefreshCcw
                  className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
                  aria-hidden="true"
                />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          <aside className="rounded-[1.8rem] border border-[#d7ddd1] bg-[#f8f5ee] p-6 dark:border-slate-800 dark:bg-slate-950/55">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
              Current Snapshot
            </p>
            <h3 className="mt-3 font-editorial text-3xl tracking-[-0.04em] text-slate-950 dark:text-white">
              Live dataset pulse
            </h3>
            <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
              The overview stays tied to the existing AtlasAI APIs and only renders analytics when
              real data is available.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {[
                `Companies: ${(dashboardQuery.dashboard?.total_companies ?? companiesQuery.totalCompanies).toLocaleString()}`,
                `Problems: ${(dashboardQuery.dashboard?.total_problems ?? problemsQuery.totalProblems).toLocaleString()}`,
                `Sectors: ${(dashboardQuery.dashboard?.total_sectors ?? sectorsQuery.totalSectors).toLocaleString()}`,
                `News: ${(dashboardQuery.dashboard?.total_news_articles ?? newsQuery.totalNews).toLocaleString()}`,
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-[#d7ddd1] bg-white/85 px-4 py-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
                >
                  {item}
                </div>
              ))}
            </div>
            {dashboardQuery.dashboard?.generated_at ? (
              <p className="mt-5 text-xs uppercase tracking-[0.18em] text-[#5d6f67] dark:text-slate-400">
                Generated {formatDate(dashboardQuery.dashboard.generated_at)}
              </p>
            ) : null}
          </aside>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => (
          <MetricCard key={card.label} {...card} />
        ))}
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-[#5d6f67] dark:text-slate-400">
            Analytics
          </p>
          <h2 className="mt-2 font-editorial text-3xl tracking-[-0.05em] text-slate-950 dark:text-white">
            Market intelligence signals
          </h2>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          {companiesQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : companiesQuery.isError ? (
            <WidgetError
              title="Companies by country unavailable"
              message="Company data failed to load."
            />
          ) : (
            <CompaniesByCountryChart data={companiesByCountryData} />
          )}

          {companiesQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : companiesQuery.isError ? (
            <WidgetError
              title="AI category chart unavailable"
              message="Company data failed to load."
            />
          ) : (
            <CompaniesByAICategoryChart data={companiesByAICategoryData} />
          )}

          {problemsQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : problemsQuery.isError ? (
            <WidgetError
              title="Problems by severity unavailable"
              message="Problem data failed to load."
            />
          ) : (
            <ProblemsBySeverityChart
              data={problemsBySeverityData}
              dataAvailable={hasProblemSeverityData}
            />
          )}

          {newsQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : newsQuery.isError ? (
            <WidgetError
              title="News timeline unavailable"
              message="News data failed to load."
            />
          ) : (
            <NewsPublishedTimelineChart data={newsTimelineData} />
          )}

          {dashboardQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : dashboardQuery.isError ? (
            <div className="xl:col-span-2">
              <WidgetEmpty
                title="Dataset coverage unavailable"
                message="Coverage metrics are only shown when the live `/dashboard` endpoint responds."
              />
            </div>
          ) : (
            <div className="xl:col-span-2">
              <DatasetCoverageChart data={coverageData} />
            </div>
          )}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <RecentSection
          title="Recent Companies"
          to="/companies"
          isLoading={companiesQuery.isLoading}
          isError={companiesQuery.isError}
          emptyMessage="No company records are available for the current dataset."
        >
          {recentCompanies.map((company) => (
            <Link
              key={company.id}
              to={`/companies/${company.id}`}
              className="flex items-start justify-between gap-4 rounded-[1.5rem] border border-[#d7ddd1] bg-white/85 px-4 py-4 transition-colors hover:bg-[#edf4ee] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-800 dark:bg-slate-950 dark:hover:bg-slate-900"
            >
              <div className="min-w-0">
                <p className="truncate text-base font-medium text-slate-950 dark:text-white">
                  {company.vendor_name}
                </p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {[company.country, company.ai_category].filter(Boolean).join(" / ") || "Company"}
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-xs uppercase tracking-[0.16em] text-[#5d6f67] dark:text-slate-400">
                  Added
                </p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {formatDate(company.created_at)}
                </p>
              </div>
            </Link>
          ))}
        </RecentSection>

        <RecentSection
          title="Latest News"
          to="/news"
          isLoading={newsQuery.isLoading}
          isError={newsQuery.isError}
          emptyMessage="No news articles are available for the current dataset."
        >
          {latestNews.map((article) => (
            <Link
              key={article.id}
              to={buildFilteredRoute("/news", article.title, article.id)}
              className="flex items-start justify-between gap-4 rounded-[1.5rem] border border-[#d7ddd1] bg-white/85 px-4 py-4 transition-colors hover:bg-[#edf4ee] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 dark:border-slate-800 dark:bg-slate-950 dark:hover:bg-slate-900"
            >
              <div className="min-w-0">
                <p className="text-base font-medium leading-6 text-slate-950 dark:text-white">
                  {article.title}
                </p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {formatArticleSource(article.url)}
                </p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-xs uppercase tracking-[0.16em] text-[#5d6f67] dark:text-slate-400">
                  Published
                </p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {formatDate(article.published_at)}
                </p>
              </div>
            </Link>
          ))}
        </RecentSection>
      </section>

      <section className="rounded-[2rem] border border-[#d7ddd1] bg-[#1f4a3a] px-6 py-6 text-[#f6f2e8] shadow-[0_28px_70px_-44px_rgba(15,23,42,0.65)] dark:border-emerald-300/15 dark:bg-emerald-950">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-emerald-100/80">
              Ask AtlasAI
            </p>
            <h2 className="mt-3 font-editorial text-3xl tracking-[-0.05em] text-[#f6f2e8]">
              Explore companies, sectors, problems, and market intelligence using AI.
            </h2>
            <p className="mt-3 text-sm leading-7 text-emerald-50/80">
              Jump from the dashboard into AtlasAI research without leaving the live dataset.
            </p>
          </div>
          <Link
            to="/ask"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#f6f2e8] px-5 py-3 text-sm font-medium text-[#214938] transition-transform hover:scale-[1.01] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <span>Ask AtlasAI</span>
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </section>
    </section>
  );
}
