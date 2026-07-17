import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import { Filter, RefreshCcw, Search, X } from "lucide-react";

import { PageContainer } from "@/components/page-container";
import { useSectors } from "@/hooks/use-sectors";
import type { Sector } from "@/types/sector";

const SECTOR_LABELS: Partial<Record<keyof Sector, string>> = {
  created_at: "Created At",
  updated_at: "Updated At",
};

function toFieldLabel(field: keyof Sector): string {
  const customLabel = SECTOR_LABELS[field];
  if (customLabel) {
    return customLabel;
  }

  return field
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatSectorFieldValue(
  field: keyof Sector,
  value: Sector[keyof Sector],
): string {
  if (!value) {
    return "—";
  }

  if (field === "created_at" || field === "updated_at") {
    return new Date(String(value)).toLocaleString();
  }

  return String(value);
}

function SectorSkeletonCard(): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="h-5 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-4 h-3 w-1/2 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-3 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    </article>
  );
}

function SectorDetailsDrawer({
  onClose,
  sector,
}: {
  onClose: () => void;
  sector: Sector;
}): ReactElement {
  const entries = Object.entries(sector) as [keyof Sector, Sector[keyof Sector]][];

  return (
    <div
      className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm"
      role="presentation"
      onClick={onClose}
    >
      <aside
        className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-950 sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-label="Sector details"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Sector record
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950 dark:text-white">
              {sector.name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sector details"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {entries.map(([field, value]) => (
            <article
              key={field}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {toFieldLabel(field)}
              </p>
              <p className="mt-2 break-words text-sm text-slate-800 dark:text-slate-200">
                {formatSectorFieldValue(field, value)}
              </p>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

export function SectorsPage(): ReactElement {
  const {
    isError,
    isLoading,
    refetch,
    searchTerm,
    sectors,
    setSearchTerm,
    totalSectors,
  } = useSectors();
  const [selectedSector, setSelectedSector] = useState<Sector | null>(null);

  useEffect(() => {
    if (!selectedSector) {
      return;
    }

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setSelectedSector(null);
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [selectedSector]);

  return (
    <PageContainer
      title="Sectors"
      subtitle="Browse sectors captured in AtlasAI and inspect their metadata."
    >
      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="relative w-full lg:max-w-md">
            <span className="sr-only">Search sectors</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search sectors"
              className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500"
            />
          </label>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              Sector Count: {totalSectors.toLocaleString()}
            </span>
            <button
              type="button"
              onClick={() => {
                void refetch();
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </button>
            <button
              type="button"
              disabled
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-400 dark:border-slate-800 dark:text-slate-500"
            >
              <Filter className="h-4 w-4" aria-hidden="true" />
              Filter
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <SectorSkeletonCard key={index} />
            ))}
          </div>
        ) : null}

        {!isLoading && isError ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-5 dark:border-red-900/60 dark:bg-red-950/30">
            <h2 className="text-base font-semibold text-red-700 dark:text-red-300">
              Unable to load sectors
            </h2>
            <p className="mt-2 text-sm text-red-600 dark:text-red-200/80">
              We could not fetch sectors from the backend. Please retry.
            </p>
            <button
              type="button"
              onClick={() => {
                void refetch();
              }}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
            >
              <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              Retry
            </button>
          </section>
        ) : null}

        {!isLoading && !isError && sectors.length === 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">
              {searchTerm.trim() ? "No matching sectors" : "No sectors available"}
            </h2>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {searchTerm.trim()
                ? "Try a broader search term."
                : "The backend returned an empty sectors dataset."}
            </p>
          </section>
        ) : null}

        {!isLoading && !isError && sectors.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {sectors.map((sector) => (
              <article
                key={sector.id}
                onClick={() => setSelectedSector(sector)}
                className="cursor-pointer rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50/40 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-800/80"
              >
                <h2 className="text-base font-semibold text-slate-950 dark:text-white">
                  {sector.name}
                </h2>
                <div className="mt-4 space-y-1 text-sm text-slate-600 dark:text-slate-300">
                  <p>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Sector ID:
                    </span>{" "}
                    {sector.id}
                  </p>
                  <p>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Created:
                    </span>{" "}
                    {formatSectorFieldValue("created_at", sector.created_at)}
                  </p>
                  <p>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Updated:
                    </span>{" "}
                    {formatSectorFieldValue("updated_at", sector.updated_at)}
                  </p>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      {selectedSector ? (
        <SectorDetailsDrawer
          onClose={() => setSelectedSector(null)}
          sector={selectedSector}
        />
      ) : null}
    </PageContainer>
  );
}
