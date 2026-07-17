import { useEffect, useMemo, useState } from "react";
import type { ReactElement } from "react";
import {
  Download,
  Filter,
  RefreshCcw,
  Search,
  Building2,
  X,
} from "lucide-react";

import { PageContainer } from "@/components/page-container";
import { useCompanies } from "@/hooks/use-companies";
import { cn } from "@/lib/utils";
import type { Company } from "@/types/company";

const FIELD_LABELS: Partial<Record<keyof Company, string>> = {
  vendor_name: "Company Name",
  ai_category: "AI Category",
  company_type: "Company Type",
  estimated_revenue: "Estimated Revenue",
  deployment_evidence: "Deployment Evidence",
  created_at: "Created At",
  updated_at: "Updated At",
};

function toFieldLabel(field: keyof Company): string {
  const customLabel = FIELD_LABELS[field];
  if (customLabel) {
    return customLabel;
  }

  return field
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function getColumnKeys(companies: Company[]): (keyof Company)[] {
  const discoveredFields = new Set<keyof Company>();

  for (const company of companies) {
    for (const field of Object.keys(company) as (keyof Company)[]) {
      discoveredFields.add(field);
    }
  }

  return [...discoveredFields];
}

function formatFieldValue(field: keyof Company, value: Company[keyof Company]): string {
  if (value === null || value === "") {
    return "—";
  }

  if (field === "created_at" || field === "updated_at") {
    return new Date(String(value)).toLocaleString();
  }

  return String(value);
}

function LoadingRows({ columnCount }: { columnCount: number }): ReactElement {
  return (
    <>
      {Array.from({ length: 6 }).map((_, index) => (
        <tr key={index} className={index % 2 === 0 ? "bg-white dark:bg-slate-900" : "bg-slate-50/60 dark:bg-slate-900/60"}>
          {Array.from({ length: columnCount }).map((__, cellIndex) => (
            <td key={cellIndex} className="px-4 py-3">
              <div className="h-4 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

function DetailsDrawer({
  company,
  onClose,
}: {
  company: Company;
  onClose: () => void;
}): ReactElement {
  const fields = Object.entries(company) as [keyof Company, Company[keyof Company]][];

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
        aria-label="Company details"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              Company profile
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950 dark:text-white">
              {company.vendor_name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close company details"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {fields.map(([field, value]) => (
            <article
              key={field}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {toFieldLabel(field)}
              </p>
              {field === "website" && typeof value === "string" && value ? (
                <a
                  href={value}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 block break-all text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  {value}
                </a>
              ) : (
                <p className="mt-2 break-words text-sm text-slate-800 dark:text-slate-200">
                  {formatFieldValue(field, value)}
                </p>
              )}
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

export function CompaniesPage(): ReactElement {
  const {
    companies,
    isError,
    isLoading,
    refetch,
    searchTerm,
    setSearchTerm,
    totalCompanies,
  } = useCompanies();
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  const columnKeys = useMemo(() => getColumnKeys(companies), [companies]);
  const loadingColumnCount = columnKeys.length > 0 ? columnKeys.length : 6;

  useEffect(() => {
    if (!selectedCompany) {
      return;
    }

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setSelectedCompany(null);
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [selectedCompany]);

  return (
    <PageContainer
      title="Companies"
      subtitle="Explore the company intelligence dataset sourced from the AtlasAI backend."
    >
      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="relative w-full lg:max-w-md">
            <span className="sr-only">Search companies by name</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by company name"
              className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500"
            />
          </label>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              <Building2 className="h-4 w-4" aria-hidden="true" />
              Total Companies: {totalCompanies.toLocaleString()}
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
            <button
              type="button"
              disabled
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-400 dark:border-slate-800 dark:text-slate-500"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Export
            </button>
          </div>
        </div>

        {isError ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-5 dark:border-red-900/60 dark:bg-red-950/30">
            <h2 className="text-base font-semibold text-red-700 dark:text-red-300">
              Unable to load companies
            </h2>
            <p className="mt-2 text-sm text-red-600 dark:text-red-200/80">
              We could not fetch the latest company data. Please try again.
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

        {!isError ? (
          <div className="overflow-hidden rounded-2xl border border-slate-200 shadow-sm dark:border-slate-800">
            <div className="max-h-[70vh] overflow-auto">
              <table className="min-w-full border-separate border-spacing-0 text-left">
                <thead className="sticky top-0 z-10 bg-slate-100 dark:bg-slate-900">
                  <tr>
                    {(isLoading ? Array.from({ length: loadingColumnCount }).map((_, index) => index) : columnKeys).map(
                      (field) => (
                        <th
                          key={String(field)}
                          className="border-b border-slate-200 px-4 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-600 dark:border-slate-800 dark:text-slate-300"
                        >
                          {typeof field === "number" ? "Loading" : toFieldLabel(field)}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? <LoadingRows columnCount={loadingColumnCount} /> : null}

                  {!isLoading && companies.length > 0
                    ? companies.map((company, rowIndex) => (
                        <tr
                          key={company.id}
                          onClick={() => setSelectedCompany(company)}
                          className={cn(
                            "cursor-pointer transition-colors",
                            rowIndex % 2 === 0
                              ? "bg-white dark:bg-slate-900"
                              : "bg-slate-50/60 dark:bg-slate-900/60",
                            "hover:bg-blue-50 dark:hover:bg-slate-800/80",
                          )}
                        >
                          {columnKeys.map((field) => (
                            <td
                              key={`${company.id}-${field}`}
                              className="border-b border-slate-200 px-4 py-3 text-sm text-slate-700 dark:border-slate-800 dark:text-slate-200"
                            >
                              {field === "website" && company[field] ? (
                                <a
                                  href={String(company[field])}
                                  target="_blank"
                                  rel="noreferrer"
                                  onClick={(event) => event.stopPropagation()}
                                  className="text-blue-600 hover:underline dark:text-blue-400"
                                >
                                  {String(company[field])}
                                </a>
                              ) : (
                                formatFieldValue(field, company[field])
                              )}
                            </td>
                          ))}
                        </tr>
                      ))
                    : null}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {!isLoading && !isError && companies.length === 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-base font-semibold text-slate-950 dark:text-white">
              {searchTerm.trim()
                ? "No matching companies"
                : "No companies available"}
            </h2>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {searchTerm.trim()
                ? "Try a different company name to broaden your search."
                : "The backend returned an empty companies dataset."}
            </p>
          </section>
        ) : null}
      </section>

      {selectedCompany ? (
        <DetailsDrawer
          company={selectedCompany}
          onClose={() => setSelectedCompany(null)}
        />
      ) : null}
    </PageContainer>
  );
}
