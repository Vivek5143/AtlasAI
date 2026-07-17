import { ChevronDown, Database, Hash, Tag } from "lucide-react";
import {
  useCallback,
  useMemo,
  useState,
  type ReactElement,
} from "react";

import { cn } from "@/lib/utils";
import type { Metadata } from "@/types/chat";

type MetadataAccordionProps = {
  metadata: Metadata[];
};

function formatScore(score?: number | null): string {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "Unavailable";
  }

  return score.toFixed(3);
}

function createMetadataRows(item: Metadata): Array<{ label: string; value: string }> {
  return [
    {
      label: "Entity Type",
      value: item.entity_type?.trim() || "Unavailable",
    },
    {
      label: "Title",
      value: item.title?.trim() || "Unavailable",
    },
    {
      label: "Similarity Score",
      value: formatScore(item.score),
    },
    {
      label: "ID",
      value: item.company_id?.trim() || item.id?.trim() || "Unavailable",
    },
  ];
}

export function MetadataAccordion({
  metadata,
}: MetadataAccordionProps): ReactElement | null {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = useCallback((): void => {
    setIsOpen((currentValue) => !currentValue);
  }, []);

  const entries = useMemo(
    () =>
      metadata.map((item, index) => ({
        id: `${item.id ?? item.company_id ?? index}`,
        rows: createMetadataRows(item),
      })),
    [metadata],
  );

  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/50">
      <button
        type="button"
        onClick={toggleOpen}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
          <Database className="h-3.5 w-3.5" aria-hidden="true" />
          Metadata
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-slate-500 transition-transform duration-200",
            isOpen ? "rotate-180" : "",
          )}
          aria-hidden="true"
        />
      </button>

      {isOpen ? (
        <div className="grid gap-3 border-t border-slate-800 px-4 py-4">
          {entries.map((entry, index) => (
            <article
              key={entry.id}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4"
            >
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
                <Tag className="h-4 w-4 text-cyan-300" aria-hidden="true" />
                Source {index + 1}
              </div>

              <dl className="grid gap-3 sm:grid-cols-2">
                {entry.rows.map((row) => (
                  <div
                    key={`${entry.id}-${row.label}`}
                    className="rounded-xl bg-slate-950/70 px-3 py-2"
                  >
                    <dt className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {row.label}
                    </dt>
                    <dd className="mt-1 flex items-start gap-2 text-sm text-slate-200">
                      {row.label === "ID" ? (
                        <Hash className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-500" />
                      ) : null}
                      <span className="break-all">{row.value}</span>
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
