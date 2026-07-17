import type { ReactElement } from "react";
import { Building2, Newspaper, RefreshCcw, Shapes, TriangleAlert } from "lucide-react";

import { PageContainer } from "@/components/page-container";
import { useDashboard } from "@/hooks/use-dashboard";
import { cn } from "@/lib/utils";
import type { DashboardMetrics } from "@/types/dashboard";

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

const secondaryMetricCards: MetricCardConfig[] = [
  {
    key: "companies_with_sectors",
    title: "Companies With Sectors",
    description: "Companies that already have sector relationships attached.",
  },
  {
    key: "companies_with_news",
    title: "Companies With News",
    description: "Companies that currently have at least one news article.",
  },
  {
    key: "sectors_with_companies",
    title: "Sectors With Companies",
    description: "Sectors that are already connected to company records.",
  },
  {
    key: "problems_with_severity",
    title: "Problems With Severity",
    description: "Problem records that already include severity metadata.",
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
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {title}
      </p>
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

function StatusCard({
  action,
  actionLabel,
  description,
  title,
  tone = "default",
}: {
  action?: () => void;
  actionLabel?: string;
  description: string;
  title: string;
  tone?: "default" | "error";
}): ReactElement {
  return (
    <section
      className={cn(
        "rounded-3xl border p-6 shadow-sm",
        tone === "error"
          ? "border-red-200 bg-red-50 dark:border-red-900/60 dark:bg-red-950/30"
          : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900",
      )}
    >
      <h2
        className={cn(
          "text-lg font-medium",
          tone === "error"
            ? "text-red-700 dark:text-red-300"
            : "text-slate-950 dark:text-white",
        )}
      >
        {title}
      </h2>
      <p
        className={cn(
          "mt-2 max-w-2xl text-sm leading-6",
          tone === "error"
            ? "text-red-600 dark:text-red-200/80"
            : "text-slate-500 dark:text-slate-400",
        )}
      >
        {description}
      </p>
      {action && actionLabel ? (
        <button
          type="button"
          onClick={action}
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          {actionLabel}
        </button>
      ) : null}
    </section>
  );
}

function SummaryStrip({
  dashboard,
}: {
  dashboard: DashboardMetrics;
}): ReactElement {
  const summaryItems = [
    {
      icon: Building2,
      label: "Companies with sector coverage",
      value: dashboard.companies_with_sectors,
    },
    {
      icon: Newspaper,
      label: "Companies with news coverage",
      value: dashboard.companies_with_news,
    },
    {
      icon: Shapes,
      label: "Sectors linked to companies",
      value: dashboard.sectors_with_companies,
    },
    {
      icon: TriangleAlert,
      label: "Problems categorized by severity",
      value: dashboard.problems_with_severity,
    },
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {summaryItems.map((item) => (
        <div
          key={item.label}
          className="flex items-start gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <item.icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-medium text-slate-950 dark:text-white">
              {item.value.toLocaleString()}
            </p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {item.label}
            </p>
          </div>
        </div>
      ))}
    </section>
  );
}

export function DashboardPage(): ReactElement {
  const { dashboard, isError, isLoading, refetch } = useDashboard();

  return (
    <PageContainer
      title="Dashboard"
      subtitle="A live overview of the AtlasAI backend metrics exposed through the dashboard API."
    >
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <LoadingSkeletonCard key={index} />
          ))}
        </div>
      ) : null}

      {!isLoading && isError ? (
        <StatusCard
          action={() => {
            void refetch();
          }}
          actionLabel="Retry"
          description="We could not load dashboard metrics from the backend right now. Please try again."
          title="Dashboard unavailable"
          tone="error"
        />
      ) : null}

      {!isLoading && !isError && !dashboard ? (
        <StatusCard
          description="The dashboard endpoint responded successfully, but there are no metrics available to display yet."
          title="No dashboard data"
        />
      ) : null}

      {!isLoading && !isError && dashboard ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {primaryMetricCards.map((card) => (
              <MetricCard
                key={card.key}
                description={card.description}
                title={card.title}
                value={dashboard[card.key] as number}
              />
            ))}
          </div>

          <SummaryStrip dashboard={dashboard} />

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
              <div className="max-w-2xl">
                <h2 className="text-lg font-medium text-slate-950 dark:text-white">
                  Coverage snapshot
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  These supporting counts show how much of the AtlasAI dataset is
                  already enriched with relationships and metadata.
                </p>
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Generated at{" "}
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  {new Date(dashboard.generated_at).toLocaleString()}
                </span>
              </p>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {secondaryMetricCards.map((card) => (
                <MetricCard
                  key={card.key}
                  description={card.description}
                  title={card.title}
                  value={dashboard[card.key] as number}
                />
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </PageContainer>
  );
}
