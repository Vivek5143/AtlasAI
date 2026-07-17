import type { ReactElement } from "react";
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";

import {
  ChartSkeletonCard,
  DatasetCoverageChart,
  NewsTimelineChart,
  ProblemsSeverityChart,
  WidgetEmpty,
  WidgetError,
  type ChartDatum,
} from "@/components/dashboard-charts";
import { PageContainer } from "@/components/page-container";
import { companiesQueryKey, useCompanies } from "@/hooks/use-companies";
import { dashboardQueryKey, useDashboard } from "@/hooks/use-dashboard";
import { newsQueryKey, useNews } from "@/hooks/use-news";
import { problemsQueryKey, useProblems } from "@/hooks/use-problems";
import { sectorsQueryKey, useSectors } from "@/hooks/use-sectors";
import type { Company } from "@/types/company";
import type { DashboardMetrics } from "@/types/dashboard";
import type { NewsArticle } from "@/types/news";
import type { Problem } from "@/types/problem";
import type { Sector } from "@/types/sector";

type MetricCardConfig = {
  description: string;
  key: keyof DashboardMetrics;
  title: string;
};

const primaryMetricCards: MetricCardConfig[] = [
  {
    key: "total_companies",
    title: "Companies",
    description: "Total companies currently stored in AtlasAI.",
  },
  {
    key: "total_problems",
    title: "Problems",
    description: "Problem definitions available for mapping and analysis.",
  },
  {
    key: "total_sectors",
    title: "Sectors",
    description: "Sector records ready for grouping and categorization.",
  },
  {
    key: "total_news_articles",
    title: "News",
    description: "Persisted news articles associated with tracked companies.",
  },
];

function MetricCard({
  description,
  title,
  value,
}: {
  description: string;
  title: string;
  value: number;
}): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
        {value.toLocaleString()}
      </p>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </article>
  );
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

function SmallStatCard({
  description,
  title,
  value,
}: {
  description: string;
  title: string;
  value: string;
}): ReactElement {
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

export function DashboardPage(): ReactElement {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const dashboardQuery = useDashboard();
  const companiesQuery = useCompanies();
  const problemsQuery = useProblems();
  const newsQuery = useNews();
  const sectorsQuery = useSectors();

  const coverageData = useMemo<ChartDatum[]>(() => {
    const dashboard = dashboardQuery.dashboard;
    if (!dashboard) {
      return [];
    }

    const values: ChartDatum[] = [];
    if (dashboard.total_companies > 0) {
      values.push({
        label: "Companies w/ Sectors",
        value: Math.round(
          (dashboard.companies_with_sectors / dashboard.total_companies) * 100,
        ),
      });
      values.push({
        label: "Companies w/ News",
        value: Math.round(
          (dashboard.companies_with_news / dashboard.total_companies) * 100,
        ),
      });
    }
    if (dashboard.total_problems > 0) {
      values.push({
        label: "Problems Categorized",
        value: Math.round(
          (dashboard.problems_with_category / dashboard.total_problems) * 100,
        ),
      });
      values.push({
        label: "Problems w/ Severity",
        value: Math.round(
          (dashboard.problems_with_severity / dashboard.total_problems) * 100,
        ),
      });
    }

    return values.filter((entry) => Number.isFinite(entry.value));
  }, [dashboardQuery.dashboard]);

  const problemsSeverityData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const problem of problemsQuery.problems) {
      const key = problem.severity?.trim() || "Unspecified";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return [...counts.entries()].map(([label, value]) => ({ label, value }));
  }, [problemsQuery.problems]);

  const newsTimelineData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const article of newsQuery.articles) {
      const date = new Date(article.published_at);
      if (Number.isNaN(date.getTime())) {
        continue;
      }
      const label = date.toISOString().slice(0, 10);
      counts.set(label, (counts.get(label) ?? 0) + 1);
    }

    return [...counts.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-12)
      .map(([label, value]) => ({ label, value }));
  }, [newsQuery.articles]);

  const quickStats = useMemo(() => {
    const totalCompanies = companiesQuery.totalCompanies;
    const totalProblems = problemsQuery.totalProblems;
    const dashboard = dashboardQuery.dashboard;

    const averageProblemsPerCompany =
      totalCompanies > 0 ? (totalProblems / totalCompanies).toFixed(2) : "—";

    const companiesWithNews = dashboard
      ? `${dashboard.companies_with_news.toLocaleString()}`
      : "—";

    const coveragePercent = dashboard
      ? (() => {
          const numerator =
            dashboard.companies_with_sectors +
            dashboard.companies_with_news +
            dashboard.problems_with_category +
            dashboard.problems_with_severity;
          const denominator =
            dashboard.total_companies * 2 + dashboard.total_problems * 2;

          if (denominator <= 0) {
            return "—";
          }

          return `${Math.round((numerator / denominator) * 100)}%`;
        })()
      : "—";

    return {
      averageProblemsPerCompany,
      companiesWithNews,
      coveragePercent,
    };
  }, [
    companiesQuery.totalCompanies,
    dashboardQuery.dashboard,
    problemsQuery.totalProblems,
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

  const anyQuickStatsLoading =
    dashboardQuery.isLoading || companiesQuery.isLoading || problemsQuery.isLoading;
  const anyActivityLoading =
    companiesQuery.isLoading || newsQuery.isLoading || problemsQuery.isLoading;
  const anyChartLoading =
    dashboardQuery.isLoading || problemsQuery.isLoading || newsQuery.isLoading;

  return (
    <PageContainer
      title="Dashboard"
      subtitle="A live analytics overview powered by AtlasAI backend datasets."
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

      {dashboardQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <LoadingSkeletonCard key={index} />
          ))}
        </div>
      ) : dashboardQuery.isError || !dashboardQuery.dashboard ? (
        <WidgetError
          title="KPI metrics unavailable"
          message="Dashboard KPI metrics could not be loaded right now."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {primaryMetricCards.map((card) => (
            <MetricCard
              key={card.key}
              description={card.description}
              title={card.title}
              value={dashboardQuery.dashboard![card.key] as number}
            />
          ))}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Quick Stats</h2>
        {anyQuickStatsLoading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <LoadingSkeletonCard key={index} />
            ))}
          </div>
        ) : dashboardQuery.isError && companiesQuery.isError && problemsQuery.isError ? (
          <WidgetError
            title="Quick stats unavailable"
            message="Required datasets failed to load."
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            <SmallStatCard
              title="Avg. Problems / Company"
              value={quickStats.averageProblemsPerCompany}
              description="Total problems divided by total companies."
            />
            <SmallStatCard
              title="Companies with News"
              value={quickStats.companiesWithNews}
              description="Company records currently linked to news articles."
            />
            <SmallStatCard
              title="Coverage"
              value={quickStats.coveragePercent}
              description="Derived enrichment coverage across companies and problems."
            />
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">Analytics</h2>
        {anyChartLoading ? (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            <ChartSkeletonCard />
            <ChartSkeletonCard />
            <ChartSkeletonCard />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {problemsQuery.isError ? (
              <WidgetError
                title="Problems chart unavailable"
                message="Problem data failed to load."
              />
            ) : (
              <ProblemsSeverityChart data={problemsSeverityData} />
            )}

            {newsQuery.isError ? (
              <WidgetError title="News chart unavailable" message="News data failed to load." />
            ) : (
              <NewsTimelineChart data={newsTimelineData} />
            )}

            {dashboardQuery.isError ? (
              <WidgetError
                title="Coverage chart unavailable"
                message="Dashboard metrics failed to load."
              />
            ) : (
              <DatasetCoverageChart data={coverageData} />
            )}
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
              Top sectors in current dataset
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
