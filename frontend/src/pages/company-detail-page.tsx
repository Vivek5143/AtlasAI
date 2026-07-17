import {
  ArrowLeft,
  Bot,
  BriefcaseBusiness,
  Building2,
  ExternalLink,
  Globe,
  Layers3,
  MapPin,
  Newspaper,
  RefreshCcw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import type { ReactElement } from "react";
import { useCallback, useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import { PageContainer } from "@/components/page-container";
import { useCompanyDetail } from "@/hooks/use-company-detail";
import type { CompanyDetail } from "@/types/company";
import type { NewsArticle } from "@/types/news";
import type { Problem } from "@/types/problem";
import type { Sector } from "@/types/sector";

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function toWebsiteHref(website: string | null): string | null {
  if (!website) {
    return null;
  }

  if (/^https?:\/\//i.test(website)) {
    return website;
  }

  return `https://${website}`;
}

function getSourceHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "External source";
  }
}

function EmptyValue({ label }: { label: string }): ReactElement {
  return (
    <p className="text-sm text-slate-500 dark:text-slate-400">
      {label} is not available in the current dataset.
    </p>
  );
}

function HeroStatCard({
  label,
  value,
}: {
  label: string;
  value: string | null;
}): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/90">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-3 text-lg font-semibold leading-7 text-slate-950 dark:text-white">
        {value?.trim() || "Unavailable"}
      </p>
    </article>
  );
}

function SectionCard({
  children,
  title,
  eyebrow,
}: {
  children: ReactElement | ReactElement[];
  title: string;
  eyebrow?: string;
}): ReactElement {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-7">
      <div className="mb-5">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-600 dark:text-cyan-300">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

function EmptyRelationshipCard({
  description,
  title,
}: {
  description: string;
  title: string;
}): ReactElement {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 p-5 dark:border-slate-700 dark:bg-slate-950/50">
      <p className="text-sm font-semibold text-slate-950 dark:text-white">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
    </div>
  );
}

function ProblemCard({ problem }: { problem: Problem }): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-amber-100 p-3 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
          <TriangleAlert className="h-4.5 w-4.5" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold leading-7 text-slate-950 dark:text-white">
            {problem.name}
          </h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {[problem.category, problem.problem_type, problem.severity]
              .filter(Boolean)
              .map((item) => (
                <span
                  key={item}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                >
                  {item}
                </span>
              ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {problem.ai_solution ||
              problem.financial_impact ||
              problem.regulatory_trigger ||
              "No additional problem context is available in the current dataset."}
          </p>
        </div>
      </div>
    </article>
  );
}

function SectorBadge({ sector }: { sector: Sector }): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/50">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-cyan-100 p-3 text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300">
          <Layers3 className="h-4.5 w-4.5" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-950 dark:text-white">{sector.name}</p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Added {formatDate(sector.created_at)}
          </p>
        </div>
      </div>
    </article>
  );
}

function NewsCard({ article }: { article: NewsArticle }): ReactElement {
  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950/50 dark:hover:border-slate-700 dark:hover:bg-slate-950">
      <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
        <span>{formatDate(article.published_at)}</span>
        <span className="h-1 w-1 rounded-full bg-slate-300 dark:bg-slate-700" />
        <span>{getSourceHost(article.url)}</span>
      </div>
      <h3 className="mt-3 text-base font-semibold leading-7 text-slate-950 dark:text-white">
        {article.title}
      </h3>
      <a
        href={article.url}
        target="_blank"
        rel="noreferrer"
        className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-cyan-700 transition-colors hover:text-cyan-600 dark:text-cyan-300 dark:hover:text-cyan-200"
      >
        Open article
        <ExternalLink className="h-4 w-4" aria-hidden="true" />
      </a>
    </article>
  );
}

function CompanyDetailSkeleton(): ReactElement {
  return (
    <PageContainer
      title="Company Profile"
      subtitle="Loading company profile from the AtlasAI backend."
    >
      <div className="space-y-6">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-7 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="h-5 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-4 h-12 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-4 h-5 w-1/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-28 animate-pulse rounded-3xl bg-slate-100 dark:bg-slate-800"
              />
            ))}
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-56 animate-pulse rounded-[2rem] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
            />
          ))}
        </div>
      </div>
    </PageContainer>
  );
}

function CompanyNotFound(): ReactElement {
  return (
    <PageContainer
      title="Company Not Found"
      subtitle="The requested company could not be found in the AtlasAI dataset."
    >
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <Building2 className="h-6 w-6" aria-hidden="true" />
        </div>
        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
          We couldn&apos;t find that company
        </h2>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-500 dark:text-slate-400">
          The company ID may be invalid, removed, or unavailable in the current backend dataset.
        </p>
        <Link
          to="/companies"
          className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to companies
        </Link>
      </section>
    </PageContainer>
  );
}

function ErrorState({
  onRetry,
}: {
  onRetry: () => Promise<void>;
}): ReactElement {
  const handleRetry = useCallback((): void => {
    void onRetry();
  }, [onRetry]);

  return (
    <PageContainer
      title="Company Profile"
      subtitle="We ran into an issue while loading this company profile."
    >
      <section className="rounded-[2rem] border border-red-200 bg-red-50 p-6 shadow-sm dark:border-red-900/50 dark:bg-red-950/20">
        <h2 className="text-lg font-semibold text-red-700 dark:text-red-300">
          Unable to load this company
        </h2>
        <p className="mt-2 text-sm leading-6 text-red-700/80 dark:text-red-200/80">
          AtlasAI could not fetch the company details from the backend. Please try again.
        </p>
        <button
          type="button"
          onClick={handleRetry}
          className="mt-5 inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Retry
        </button>
      </section>
    </PageContainer>
  );
}

function CompanyHero({ company }: { company: CompanyDetail }): ReactElement {
  const websiteHref = toWebsiteHref(company.website);

  return (
    <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_right,_rgba(6,182,212,0.18),_transparent_28%),linear-gradient(135deg,_rgba(255,255,255,1)_0%,_rgba(248,250,252,1)_100%)] p-7 shadow-sm dark:border-slate-800 dark:bg-[radial-gradient(circle_at_top_right,_rgba(6,182,212,0.18),_transparent_28%),linear-gradient(135deg,_rgba(15,23,42,1)_0%,_rgba(2,6,23,1)_100%)] sm:p-8">
      <div className="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-700 dark:text-cyan-200">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            Company Profile
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-4xl">
            {company.vendor_name}
          </h1>

          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900/80">
              <MapPin className="h-4 w-4 text-cyan-700 dark:text-cyan-300" aria-hidden="true" />
              {company.country?.trim() || "Country unavailable"}
            </span>

            {websiteHref ? (
              <a
                href={websiteHref}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 font-medium text-slate-700 transition-colors hover:border-cyan-300 hover:text-cyan-700 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-200 dark:hover:border-cyan-500 dark:hover:text-cyan-200"
              >
                <Globe className="h-4 w-4 text-cyan-700 dark:text-cyan-300" aria-hidden="true" />
                <span className="max-w-[16rem] truncate">{company.website}</span>
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
              </a>
            ) : (
              <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900/80">
                <Globe className="h-4 w-4 text-cyan-700 dark:text-cyan-300" aria-hidden="true" />
                Website unavailable
              </span>
            )}
          </div>
        </div>

        <div className="grid w-full gap-4 md:grid-cols-2 xl:max-w-2xl xl:grid-cols-2">
          <HeroStatCard label="Funding" value={company.funding} />
          <HeroStatCard label="Revenue" value={company.estimated_revenue} />
          <HeroStatCard label="Maturity" value={company.maturity} />
          <HeroStatCard label="AI Category" value={company.ai_category} />
        </div>
      </div>
    </section>
  );
}

export function CompanyDetailPage(): ReactElement {
  const { companyId } = useParams<{ companyId: string }>();
  const {
    company,
    companyError,
    companyLoading,
    companyNotFound,
    refetchCompany,
  } = useCompanyDetail(companyId);

  const handleRetry = useCallback(async (): Promise<void> => {
    await refetchCompany();
  }, [refetchCompany]);

  const askState = useMemo(
    () =>
      company
        ? {
            initialQuestion: `Tell me about ${company.vendor_name}`,
          }
        : undefined,
    [company],
  );

  if (!companyId) {
    return <CompanyNotFound />;
  }

  if (companyLoading) {
    return <CompanyDetailSkeleton />;
  }

  if (companyNotFound) {
    return <CompanyNotFound />;
  }

  if (companyError || !company) {
    return <ErrorState onRetry={handleRetry} />;
  }

  return (
    <>
      <PageContainer
        title="Company Profile"
        subtitle="Deep dive into a single company using the live AtlasAI backend company relationships now exposed through the detail endpoint."
      >
        <div className="space-y-6">
          <CompanyHero company={company} />

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <SectionCard title="Overview" eyebrow="Snapshot">
              <div className="grid gap-4 md:grid-cols-2">
                <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-white">
                    <BriefcaseBusiness className="h-4 w-4 text-cyan-700 dark:text-cyan-300" />
                    Company Type
                  </div>
                  {company.company_type ? (
                    <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                      {company.company_type}
                    </p>
                  ) : (
                    <div className="mt-3">
                      <EmptyValue label="Company type" />
                    </div>
                  )}
                </article>

                <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-white">
                    <Building2 className="h-4 w-4 text-cyan-700 dark:text-cyan-300" />
                    Dataset Record
                  </div>
                  <dl className="mt-3 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                    <div>
                      <dt className="font-medium text-slate-950 dark:text-white">Created</dt>
                      <dd>{formatDate(company.created_at)}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-slate-950 dark:text-white">Updated</dt>
                      <dd>{formatDate(company.updated_at)}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-slate-950 dark:text-white">Company ID</dt>
                      <dd className="break-all">{company.id}</dd>
                    </div>
                  </dl>
                </article>
              </div>
            </SectionCard>

            <SectionCard title="Deployment Evidence" eyebrow="Signal">
              {company.deployment_evidence ? (
                <div className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
                  <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700 dark:text-slate-300">
                    {company.deployment_evidence}
                  </p>
                </div>
              ) : (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 p-5 dark:border-slate-700 dark:bg-slate-950/50">
                  <EmptyValue label="Deployment evidence" />
                </div>
              )}
            </SectionCard>
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard title="Problems Solved" eyebrow="Relationships">
              {company.problems.length > 0 ? (
                <div className="grid gap-4">
                  {company.problems.map((problem) => (
                    <ProblemCard key={problem.id} problem={problem} />
                  ))}
                </div>
              ) : (
                <EmptyRelationshipCard
                  title="No linked problems found"
                  description="This company does not currently have any problem mappings in the dataset."
                />
              )}
            </SectionCard>

            <SectionCard title="Industries" eyebrow="Relationships">
              {company.sectors.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {company.sectors.map((sector) => (
                    <SectorBadge key={sector.id} sector={sector} />
                  ))}
                </div>
              ) : (
                <EmptyRelationshipCard
                  title="No linked sectors found"
                  description="This company does not currently have any sector associations in the dataset."
                />
              )}
            </SectionCard>
          </div>

          <SectionCard title="Related News" eyebrow="Coverage">
            {company.news.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {company.news.map((article) => (
                  <NewsCard key={article.id} article={article} />
                ))}
              </div>
            ) : (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50/80 p-6 dark:border-slate-700 dark:bg-slate-950/50">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-slate-200 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    <Newspaper className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-950 dark:text-white">
                      No related news found
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                      This company does not currently have any linked news articles in the dataset.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </SectionCard>
        </div>
      </PageContainer>

      <Link
        to="/ask"
        state={askState}
        className="fixed bottom-6 right-4 z-30 inline-flex items-center gap-3 rounded-full bg-slate-950 px-5 py-3.5 text-sm font-medium text-white shadow-[0_24px_60px_-24px_rgba(8,145,178,0.7)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 dark:bg-cyan-400 dark:text-slate-950 dark:hover:bg-cyan-300 sm:bottom-8 sm:right-8"
      >
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-white/10 dark:bg-slate-950/10">
          <Bot className="h-5 w-5" aria-hidden="true" />
        </span>
        <span className="flex flex-col text-left">
          <span className="text-xs uppercase tracking-[0.18em] text-white/70 dark:text-slate-950/70">
            Ask AtlasAI
          </span>
          <span className="text-sm font-semibold">Tell me about this company</span>
        </span>
      </Link>
    </>
  );
}
