import type { ReactElement } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type ChartDatum = {
  label: string;
  value: number;
};

type ChartCardProps = {
  children: ReactElement;
  description: string;
  title: string;
};

function ChartCard({ children, description, title }: ChartCardProps): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-base font-semibold text-slate-950 dark:text-white">{title}</h3>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
      <div className="mt-4 h-64">{children}</div>
    </article>
  );
}

export function ChartSkeletonCard(): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="h-5 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-4 h-56 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    </article>
  );
}

export function WidgetError({
  message,
  title,
}: {
  message: string;
  title: string;
}): ReactElement {
  return (
    <div className="flex h-full min-h-52 items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 py-6 text-center dark:border-red-900/60 dark:bg-red-950/30">
      <div>
        <p className="font-medium text-red-700 dark:text-red-300">{title}</p>
        <p className="mt-1 text-sm text-red-600 dark:text-red-200/80">{message}</p>
      </div>
    </div>
  );
}

export function WidgetEmpty({
  message,
  title,
}: {
  message: string;
  title: string;
}): ReactElement {
  return (
    <div className="flex h-full min-h-52 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-center dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="font-medium text-slate-900 dark:text-white">{title}</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{message}</p>
      </div>
    </div>
  );
}

export function ProblemsSeverityChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="Problems by Severity"
        description="Distribution of problems grouped by severity."
      >
        <WidgetEmpty
          title="No severity data"
          message="Severity values are not available in the current problem dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Problems by Severity"
      description="Distribution of problems grouped by severity."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function NewsTimelineChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="News Published Timeline"
        description="Recent article volume by publish date."
      >
        <WidgetEmpty
          title="No timeline data"
          message="Published timestamps are not available in the current news dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="News Published Timeline"
      description="Recent article volume by publish date."
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#0f766e"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function DatasetCoverageChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="Dataset Coverage"
        description="Coverage ratios derived from current enrichment metrics."
      >
        <WidgetEmpty
          title="No coverage data"
          message="Coverage metrics are unavailable from the dashboard response."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Dataset Coverage"
      description="Coverage ratios derived from current enrichment metrics."
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={90}
            fill="#2563eb"
            label
          />
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
