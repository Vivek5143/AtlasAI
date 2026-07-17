import type { ReactElement } from "react";
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  BadgeAlert,
  Building2,
  Layers3,
  Newspaper,
  RefreshCcw,
} from "lucide-react";

import {
  ChartSkeletonCard,
  CompaniesByAICategoryChart,
  CompaniesByCountryChart,
  LatestNewsTimelineChart,
  ProblemsByIndustryChart,
  WidgetError,
  WidgetEmpty,
  type ChartDatum,
} from "@/components/dashboard-charts";
import { PageContainer } from "@/components/page-container";
import { companiesQueryKey, useCompanies } from "@/hooks/use-companies";
import { newsQueryKey, useNews } from "@/hooks/use-news";
import { problemsQueryKey, useProblems } from "@/hooks/use-problems";
import { sectorsQueryKey, useSectors } from "@/hooks/use-sectors";
import type { Company } from "@/types/company";
import type { NewsArticle } from "@/types/news";
import type { Problem } from "@/types/problem";
import type { Sector } from "@/types/sector";

type MetricCardProps = {
  description: string;
  icon: ReactElement;
  isLoading: boolean;
  title: string;
  value: number;
};

type SmallStatCardProps = {
  description: string;
  title: string;
  value: string;
};

function normalizeLabel(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
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

function sortLatest<T>(
  items: T[],
  dateSelector: (item: T) => string,
  textSelector: (item: T) => string,
): string[] {
  return [...items]
    .sort(
      (a, b) =>
        new Date(dateSelector(b)).getTime() - new Date(dateSelector(a)).getTime(),
    )
    .slice(0, 5)
    .map((item) => textSelector(item));
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

function LoadingSkeletonCard(): ReactElement {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="h-4 w-28 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-4 h-10 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-3 h-4 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-4 w-4/5 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}

function MetricCard({
  description,
  icon,
  isLoading,
  title,
  value,
}: MetricCardProps): ReactElement {
  if (isLoading) {
    return <LoadingSkeletonCard />;
  }

  return (
    <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {value.toLocaleString()}
          </p>
        </div>
        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          {icon}
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
    </article>
  );
}

function SmallStatCard({
  description,
  title,
  value,
}: SmallStatCardProps): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {title}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{value}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
    </article>
  );
}

function ActivityListSkeleton(): ReactElement {
  return (
    <div className="space-y-2 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {Array.from({ length: 5 }).map((_, idx) => (
        <div
          key={idx}
          className="h-10 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-800"
        />
      ))}
    </div>
  );
}

function ActivityListCard({
  items,
  title,
}: {
  items: string[];
  title: string;
}): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-base font-semibold text-slate-950 dark:text-white">{title}</h3>
      {items.length ? (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li
              key={item}
              className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-3">
          <WidgetEmpty title="No items" message="No records available for this widget." />
        </div>
      )}
    </article>
  );
}

export function DashboardPage(): ReactElement {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const companiesQuery = useCompanies();
  const problemsQuery = useProblems();
  const newsQuery = useNews();
  const sectorsQuery = useSectors();

  const metricCards = useMemo(
    () => [
      {
        title: "Total Companies",
        value: companiesQuery.totalCompanies,
        isLoading: companiesQuery.isLoading,
        description: "Tracked companies currently available in AtlasAI.",
        icon: <Building2 className="h-5 w-5" aria-hidden="true" />,
      },
      {
        title: "Total Problems",
        value: problemsQuery.totalProblems,
        isLoading: problemsQuery.isLoading,
        description: "Problem records ready for analysis and mapping.",
        icon: <BadgeAlert className="h-5 w-5" aria-hidden="true" />,
      },
      {
        title: "Total News",
        value: newsQuery.totalNews,
        isLoading: newsQuery.isLoading,
        description: "Persisted news articles connected to tracked companies.",
        icon: <Newspaper className="h-5 w-5" aria-hidden="true" />,
      },
      {
        title: "Total Sectors",
        value: sectorsQuery.totalSectors,
        isLoading: sectorsQuery.isLoading,
        description: "Sector records available for grouping and discovery.",
        icon: <Layers3 className="h-5 w-5" aria-hidden="true" />,
      },
    ],
    [
      companiesQuery.isLoading,
      companiesQuery.totalCompanies,
      newsQuery.isLoading,
      newsQuery.totalNews,
      problemsQuery.isLoading,
      problemsQuery.totalProblems,
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

  const hasProblemIndustryData = useMemo(
    () => problemsQuery.problems.some((problem) => Boolean(normalizeLabel(problem.industry))),
    [problemsQuery.problems],
  );

  const problemsByIndustryData = useMemo(
    () =>
      aggregateByLabel(problemsQuery.problems, (problem) => problem.industry, {
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

  const quickStats = useMemo(() => {
    const averageNewsPerCompany =
      companiesQuery.totalCompanies > 0
        ? (newsQuery.totalNews / companiesQuery.totalCompanies).toFixed(2)
        : "N/A";

    const companiesWithKnownCountry = companiesQuery.companies.filter((company) =>
      Boolean(normalizeLabel(company.country)),
    ).length;
    const countryCoverage =
      companiesQuery.totalCompanies > 0
        ? `${Math.round((companiesWithKnownCountry / companiesQuery.totalCompanies) * 100)}%`
        : "N/A";

    const companiesWithKnownCategory = companiesQuery.companies.filter((company) =>
      Boolean(normalizeLabel(company.ai_category)),
    ).length;
    const categoryCoverage =
      companiesQuery.totalCompanies > 0
        ? `${Math.round((companiesWithKnownCategory / companiesQuery.totalCompanies) * 100)}%`
        : "N/A";

    return {
      averageNewsPerCompany,
      categoryCoverage,
      countryCoverage,
    };
  }, [
    companiesQuery.companies,
    companiesQuery.totalCompanies,
    newsQuery.totalNews,
  ]);

  const latestCompanies = useMemo(
    () =>
      sortLatest<Company>(
        companiesQuery.companies,
        (company) => company.created_at,
        (company) => company.vendor_name,
      ),
    [companiesQuery.companies],
  );

  const latestNews = useMemo(
    () =>
      sortLatest<NewsArticle>(
        newsQuery.articles,
        (article) => article.published_at,
        (article) => article.title,
      ),
    [newsQuery.articles],
  );

  const latestProblems = useMemo(
    () =>
      sortLatest<Problem>(
        problemsQuery.problems,
        (problem) => problem.created_at,
        (problem) => problem.name,
      ),
    [problemsQuery.problems],
  );

  const handleRefreshDashboard = async (): Promise<void> => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: companiesQueryKey }),
        queryClient.invalidateQueries({ queryKey: problemsQueryKey }),
        queryClient.invalidateQueries({ queryKey: sectorsQueryKey }),
        queryClient.invalidateQueries({ queryKey: newsQueryKey }),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const anyQuickStatsLoading =
    companiesQuery.isLoading || newsQuery.isLoading || sectorsQuery.isLoading;
  const anyActivityLoading =
    companiesQuery.isLoading || newsQuery.isLoading || problemsQuery.isLoading;

  return (
    <PageContainer
      title="Dashboard"
      subtitle="A live analytics overview powered by AtlasAI frontend datasets."
    >
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => {
            void handleRefreshDashboard();
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <RefreshCcw
            className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            aria-hidden="true"
          />
          Refresh Dashboard
        </button>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => (
          <MetricCard key={card.title} {...card} />
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Charts</h2>
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
              title="Problems by industry unavailable"
              message="Problem data failed to load."
            />
          ) : (
            <ProblemsByIndustryChart
              data={problemsByIndustryData}
              dataAvailable={hasProblemIndustryData}
            />
          )}

          {newsQuery.isLoading ? (
            <ChartSkeletonCard />
          ) : newsQuery.isError ? (
            <WidgetError
              title="Latest news timeline unavailable"
              message="News data failed to load."
            />
          ) : (
            <LatestNewsTimelineChart data={newsTimelineData} />
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Quick Stats</h2>
        {anyQuickStatsLoading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <LoadingSkeletonCard key={index} />
            ))}
          </div>
        ) : companiesQuery.isError && newsQuery.isError && sectorsQuery.isError ? (
          <WidgetError
            title="Quick stats unavailable"
            message="Required datasets failed to load."
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            <SmallStatCard
              title="Avg. News / Company"
              value={quickStats.averageNewsPerCompany}
              description="Total news articles divided by total companies."
            />
            <SmallStatCard
              title="Country Coverage"
              value={quickStats.countryCoverage}
              description="Companies that currently include a country value."
            />
            <SmallStatCard
              title="AI Category Coverage"
              value={quickStats.categoryCoverage}
              description="Companies that currently include an AI category."
            />
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Recent Activity</h2>
        {anyActivityLoading ? (
          <div className="grid gap-4 lg:grid-cols-3">
            <ActivityListSkeleton />
            <ActivityListSkeleton />
            <ActivityListSkeleton />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {companiesQuery.isError ? (
              <WidgetError
                title="Latest companies unavailable"
                message="Company data failed to load."
              />
            ) : (
              <ActivityListCard title="Latest Companies" items={latestCompanies} />
            )}

            {newsQuery.isError ? (
              <WidgetError title="Latest news unavailable" message="News data failed to load." />
            ) : (
              <ActivityListCard title="Latest News" items={latestNews} />
            )}

            {problemsQuery.isError ? (
              <WidgetError
                title="Newest problems unavailable"
                message="Problem data failed to load."
              />
            ) : (
              <ActivityListCard title="Newest Problems" items={latestProblems} />
            )}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Dataset Snapshot</h2>
        {sectorsQuery.isLoading ? (
          <LoadingSkeletonCard />
        ) : sectorsQuery.isError ? (
          <WidgetError title="Snapshot unavailable" message="Sector data failed to load." />
        ) : sectorsQuery.sectors.length ? (
          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Top sectors in the current dataset
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {sectorsQuery.sectors.slice(0, 10).map((sector: Sector) => (
                <span
                  key={sector.id}
                  className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  {sector.name}
                </span>
              ))}
            </div>
          </article>
        ) : (
          <WidgetEmpty
            title="No sectors available"
            message="Sector distribution cannot be rendered without sector data."
          />
        )}
      </section>
    </PageContainer>
  );
}
