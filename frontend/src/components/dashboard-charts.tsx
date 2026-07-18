import type { ReactElement, ReactNode } from "react";
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
  detail?: string;
  label: string;
  value: number;
};

type ChartCardProps = {
  children: ReactNode;
  description: string;
  title: string;
};

const PIE_COLORS = [
  "#214938",
  "#3f6a56",
  "#6c8e7a",
  "#96ab9f",
  "#c4d0c3",
  "#a98065",
  "#6b7d86",
  "#d4d9d0",
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
    <article className="rounded-[1.9rem] border border-[#d7ddd1] bg-[#fcfaf6] p-5 shadow-[0_24px_60px_-42px_rgba(15,23,42,0.38)] dark:border-slate-800 dark:bg-slate-900">
      <h3 className="font-editorial text-2xl tracking-[-0.04em] text-slate-950 dark:text-white">
        {title}
      </h3>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
      <div className="mt-4 h-72">{children}</div>
    </article>
  );
}

function DefaultTooltip({
  active,
  label,
  payload,
  valueFormatter,
}: {
  active?: boolean;
  label?: string;
  payload?: Array<{ payload?: ChartDatum; value?: number }>;
  valueFormatter?: (value: number, item?: ChartDatum) => string;
}): ReactElement | null {
  if (!active || !payload?.length) {
    return null;
  }

  const value = typeof payload[0]?.value === "number" ? payload[0].value : 0;
  const item = payload[0]?.payload;

  return (
    <div className="rounded-2xl border border-[#d7ddd1] bg-white px-3 py-2 shadow-lg dark:border-slate-700 dark:bg-slate-950">
      <p className="text-sm font-medium text-slate-950 dark:text-white">{label}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        {valueFormatter ? valueFormatter(value, item) : `${value.toLocaleString()} records`}
      </p>
    </div>
  );
}

export function ChartSkeletonCard(): ReactElement {
  return (
    <article className="rounded-[1.9rem] border border-[#d7ddd1] bg-[#fcfaf6] p-5 shadow-[0_24px_60px_-42px_rgba(15,23,42,0.38)] dark:border-slate-800 dark:bg-slate-900">
      <div className="h-5 w-1/2 animate-pulse rounded bg-[#dde5dc] dark:bg-slate-800" />
      <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-[#e6ece4] dark:bg-slate-800" />
      <div className="mt-4 h-64 animate-pulse rounded bg-[#eef2ea] dark:bg-slate-800" />
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
    <div className="flex h-full min-h-56 items-center justify-center rounded-[1.6rem] border border-red-200 bg-red-50 px-4 py-6 text-center dark:border-red-900/60 dark:bg-red-950/30">
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
    <div className="flex h-full min-h-56 items-center justify-center rounded-[1.6rem] border border-[#d7ddd1] bg-[#f6f5f0] px-4 py-6 text-center dark:border-slate-800 dark:bg-slate-900">
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
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#d7ddd1" />
          <XAxis
            type="number"
            allowDecimals={false}
            tickFormatter={formatCompactNumber}
            stroke="#66746d"
          />
          <YAxis
            type="category"
            dataKey="label"
            width={110}
            tickFormatter={(value: string) => truncateLabel(value, 14)}
            stroke="#66746d"
          />
          <Tooltip content={<DefaultTooltip />} cursor={{ fill: "rgba(33, 73, 56, 0.08)" }} />
          <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#214938" />
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

export function ProblemsBySeverityChart({
  data,
  dataAvailable,
}: {
  data: ChartDatum[];
  dataAvailable: boolean;
}): ReactElement {
  if (!dataAvailable) {
    return (
      <ChartCard
        title="Problems by Severity"
        description="Severity distribution for problems currently available to the dashboard."
      >
        <WidgetEmpty
          title="Severity data unavailable"
          message="Problem severity values are not available in the current dataset."
        />
      </ChartCard>
    );
  }

  if (!data.length) {
    return (
      <ChartCard
        title="Problems by Severity"
        description="Severity distribution for problems currently available to the dashboard."
      >
        <WidgetEmpty
          title="No severity values"
          message="Problem severity values are empty in the current dataset."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Problems by Severity"
      description="Severity distribution for problems currently available to the dashboard."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d7ddd1" />
          <XAxis
            dataKey="label"
            tickFormatter={(value: string) => truncateLabel(value, 12)}
            stroke="#66746d"
          />
          <YAxis allowDecimals={false} stroke="#66746d" />
          <Tooltip content={<DefaultTooltip />} />
          <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#6f8f7b" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function NewsPublishedTimelineChart({
  data,
}: {
  data: ChartDatum[];
}): ReactElement {
  if (!data.length) {
    return (
      <ChartCard
        title="News Published Timeline"
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
      title="News Published Timeline"
      description="Daily news volume across the most recent publish dates."
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <defs>
            <linearGradient id="newsTimelineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#214938" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#214938" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d7ddd1" />
          <XAxis dataKey="label" stroke="#66746d" />
          <YAxis allowDecimals={false} stroke="#66746d" />
          <Tooltip content={<DefaultTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#214938"
            strokeWidth={2}
            fill="url(#newsTimelineGradient)"
          />
        </AreaChart>
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
        description="Coverage signals exposed by the live AtlasAI dashboard metrics endpoint."
      >
        <WidgetEmpty
          title="No coverage metrics"
          message="Coverage metrics are not available in the current dashboard response."
        />
      </ChartCard>
    );
  }

  return (
    <ChartCard
      title="Dataset Coverage"
      description="Coverage signals exposed by the live AtlasAI dashboard metrics endpoint."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 12, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#d7ddd1" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(value: number) => `${value}%`}
            stroke="#66746d"
          />
          <YAxis
            type="category"
            dataKey="label"
            width={150}
            tickFormatter={(value: string) => truncateLabel(value, 18)}
            stroke="#66746d"
          />
          <Tooltip
            content={
              <DefaultTooltip
                valueFormatter={(value, item) =>
                  item?.detail
                    ? `${value}% covered / ${item.detail}`
                    : `${value}% covered`
                }
              />
            }
          />
          <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#3f6a56" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
