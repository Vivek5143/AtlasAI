import type { ReactNode, ReactElement } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
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
  children: ReactNode;
  description: string;
  title: string;
};

const PIE_COLORS = [
  "#0f766e",
  "#2563eb",
  "#ea580c",
  "#7c3aed",
  "#ca8a04",
  "#0891b2",
  "#be123c",
  "#4f46e5",
];

function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function truncateLabel(label: string, maxLength = 18): string {
  if (label.length <= maxLength) {
    return label;
  }

  return `${label.slice(0, maxLength - 1)}...`;
}

function ChartCard({ children, description, title }: ChartCardProps): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-base font-semibold text-slate-950 dark:text-white">{title}</h3>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
      <div className="mt-4 h-72">{children}</div>
    </article>
  );
}

function DefaultTooltip({
  active,
  label,
  payload,
}: {
  active?: boolean;
  label?: string;
  payload?: Array<{ value?: number }>;
}): ReactElement | null {
  if (!active || !payload?.length) {
    return null;
  }

  const value = typeof payload[0]?.value === "number" ? payload[0].value : 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-lg dark:border-slate-700 dark:bg-slate-950">
      <p className="text-sm font-medium text-slate-950 dark:text-white">{label}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {value.toLocaleString()} records
      </p>
    </div>
  );
}

export function ChartSkeletonCard(): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="h-5 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-4 h-64 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
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
    <div className="flex h-full min-h-56 items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 py-6 text-center dark:border-red-900/60 dark:bg-red-950/30">
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
    <div className="flex h-full min-h-56 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-center dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="font-medium text-slate-900 dark:text-white">{title}</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{message}</p>
      </div>
    </div>
  );
}

export function CompaniesByCountryChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="Companies by Country"
        description="Top countries represented across tracked companies."
      >
        <WidgetEmpty
          title="No country data"
          message="Company country values are not available in the current dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Companies by Country"
      description="Top countries represented across tracked companies."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#cbd5e1" />
          <XAxis
            type="number"
            allowDecimals={false}
            tickFormatter={formatCompactNumber}
            stroke="#64748b"
          />
          <YAxis
            type="category"
            dataKey="label"
            width={110}
            tickFormatter={(value: string) => truncateLabel(value, 14)}
            stroke="#64748b"
          />
          <Tooltip content={<DefaultTooltip />} cursor={{ fill: "rgba(37, 99, 235, 0.08)" }} />
          <Bar dataKey="value" radius={[0, 10, 10, 0]} fill="#2563eb" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function CompaniesByAICategoryChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="Companies by AI Category"
        description="Distribution of companies across AI categories."
      >
        <WidgetEmpty
          title="No category data"
          message="AI category values are not available in the current company dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Companies by AI Category"
      description="Distribution of companies across AI categories."
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="46%"
            innerRadius={58}
            outerRadius={92}
            paddingAngle={3}
            label={({ percent }) =>
              typeof percent === "number" ? `${Math.round(percent * 100)}%` : ""
            }
          >
            {data.map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<DefaultTooltip />} />
          <Legend
            verticalAlign="bottom"
            formatter={(value: string) => truncateLabel(value, 24)}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function ProblemsByIndustryChart({
  data,
  dataAvailable,
}: {
  data: ChartDatum[];
  dataAvailable: boolean;
}): ReactElement {
  if (!dataAvailable) {
    return (
      <ChartCard
        title="Problems by Industry"
        description="Industry distribution for problems currently available to the dashboard."
      >
        <WidgetEmpty
          title="Industry data needs backend support"
          message="The current problem API does not expose an industry field, so this chart will populate once `/problems` includes one."
        />
      </ChartCard>
    );
  }

  if (!data.length) {
    return (
      <ChartCard
        title="Problems by Industry"
        description="Industry distribution for problems currently available to the dashboard."
      >
        <WidgetEmpty
          title="No industry data"
          message="Problem industry values are empty in the current dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Problems by Industry"
      description="Industry distribution for problems currently available to the dashboard."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#cbd5e1" />
          <XAxis dataKey="label" tickFormatter={(value: string) => truncateLabel(value, 12)} stroke="#64748b" />
          <YAxis allowDecimals={false} stroke="#64748b" />
          <Tooltip content={<DefaultTooltip />} />
          <Bar dataKey="value" radius={[10, 10, 0, 0]} fill="#ea580c" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function LatestNewsTimelineChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="Latest News Timeline"
        description="Daily news volume across the most recent publish dates."
      >
        <WidgetEmpty
          title="No news timeline"
          message="Published timestamps are not available in the current news dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Latest News Timeline"
      description="Daily news volume across the most recent publish dates."
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <defs>
            <linearGradient id="newsTimelineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0891b2" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#0891b2" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#cbd5e1" />
          <XAxis dataKey="label" stroke="#64748b" />
          <YAxis allowDecimals={false} stroke="#64748b" />
          <Tooltip content={<DefaultTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#0891b2"
            strokeWidth={2}
            fill="url(#newsTimelineGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
