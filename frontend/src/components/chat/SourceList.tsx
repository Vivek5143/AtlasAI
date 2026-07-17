import { ArrowUpRight, FileText } from "lucide-react";
import type { ReactElement } from "react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import type { Source } from "@/types/chat";

type SourceListProps = {
  sources: Source[];
};

function SourceLink({ source }: { source: Source }): ReactElement {
  const sharedClasses =
    "group flex items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 px-4 py-3 text-left transition-all duration-200 hover:border-slate-700 hover:bg-slate-800/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400";

  const content = (
    <>
      <span className="flex min-w-0 items-center gap-3">
        <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-cyan-200">
          <FileText className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block truncate text-sm font-medium text-white">
            {source.title}
          </span>
          <span className="block truncate text-xs text-slate-400">
            {source.entityType ?? "source"}
          </span>
        </span>
      </span>
      <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-500 transition-colors group-hover:text-cyan-300" />
    </>
  );

  if (source.href) {
    return (
      <Link to={source.href} className={sharedClasses}>
        {content}
      </Link>
    );
  }

  return <div className={cn(sharedClasses, "cursor-default")}>{content}</div>;
}

export function SourceList({ sources }: SourceListProps): ReactElement | null {
  if (sources.length === 0) {
    return null;
  }

  return (
    <section className="mt-4 space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        <FileText className="h-3.5 w-3.5" aria-hidden="true" />
        Sources
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {sources.map((source) => (
          <SourceLink key={source.id} source={source} />
        ))}
      </div>
    </section>
  );
}
