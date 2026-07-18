import { useMutation, useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  ExternalLink,
  Loader2,
  RefreshCcw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useMemo, useState, type FormEvent, type ReactElement } from "react";

import { PageContainer } from "@/components/page-container";
import {
  approveDiscoveryCandidate,
  getPendingDiscoveryCandidates,
  rejectDiscoveryCandidate,
  searchDiscoveryCandidates,
} from "@/services/discovery";
import type {
  CompanyDiscoveryCandidate,
  CompanyDiscoverySearchResponse,
} from "@/types/discovery";

const pendingDiscoveryQueryKey = ["discovery", "pending"] as const;

type ReviewMessage = {
  tone: "success" | "error";
  text: string;
};

type ReviewTarget = {
  candidate: CompanyDiscoveryCandidate;
  reason: string;
};

function formatOptional(value: string | null | undefined): string {
  return value?.trim() ? value : "Not available";
}

function formatConfidence(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function SummaryMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}): ReactElement {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
        {value.toLocaleString()}
      </p>
    </div>
  );
}

function CandidateCard({
  candidate,
  isApproving,
  isRejecting,
  onApprove,
  onReject,
}: {
  candidate: CompanyDiscoveryCandidate;
  isApproving: boolean;
  isRejecting: boolean;
  onApprove: (candidate: CompanyDiscoveryCandidate) => void;
  onReject: (candidate: CompanyDiscoveryCandidate) => void;
}): ReactElement {
  const isPending = candidate.status === "pending";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-950 dark:text-white">
              {candidate.company_name}
            </h3>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium capitalize text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
              {candidate.status}
            </span>
            <span className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-300">
              Confidence: {formatConfidence(candidate.confidence_score)}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {formatOptional(candidate.description)}
          </p>
        </div>

        {isPending ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onApprove(candidate)}
              disabled={isApproving || isRejecting}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-700 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isApproving ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
              )}
              Approve
            </button>
            <button
              type="button"
              onClick={() => onReject(candidate)}
              disabled={isApproving || isRejecting}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 px-3 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900/70 dark:text-red-300 dark:hover:bg-red-950/30"
            >
              {isRejecting ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <XCircle className="h-4 w-4" aria-hidden="true" />
              )}
              Reject
            </button>
          </div>
        ) : null}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
            Country
          </p>
          <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">
            {formatOptional(candidate.country)}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
            AI Category
          </p>
          <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">
            {formatOptional(candidate.ai_category)}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
            Source Domain
          </p>
          <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">
            {formatOptional(candidate.source_domain)}
          </p>
        </div>
      </div>

      <section className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/45">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
              Evidence
            </p>
            <h4 className="mt-1 text-sm font-semibold leading-6 text-slate-950 dark:text-white">
              {formatOptional(candidate.evidence_title)}
            </h4>
          </div>
          <a
            href={candidate.evidence_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            View Evidence
          </a>
        </div>
        <p className="mt-3 break-all text-xs text-slate-500 dark:text-slate-400">
          {candidate.evidence_url}
        </p>
      </section>

      {candidate.confidence_reasons.length > 0 ? (
        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
            Confidence Reasons
          </p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {candidate.confidence_reasons.map((reason) => (
              <li
                key={reason}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300"
              >
                {reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}

function RejectDialog({
  error,
  isSubmitting,
  onCancel,
  onReasonChange,
  onSubmit,
  target,
}: {
  error: string | null;
  isSubmitting: boolean;
  onCancel: () => void;
  onReasonChange: (value: string) => void;
  onSubmit: () => void;
  target: ReviewTarget;
}): ReactElement {
  const reasonIsEmpty = !target.reason.trim();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 backdrop-blur-sm">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="reject-discovery-title"
        className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-950"
      >
        <h2
          id="reject-discovery-title"
          className="text-lg font-semibold text-slate-950 dark:text-white"
        >
          Reject {target.candidate.company_name}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Add a review reason before removing this candidate from the pending queue.
        </p>
        <label className="mt-4 block">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
            Rejection Reason
          </span>
          <textarea
            value={target.reason}
            onChange={(event) => onReasonChange(event.target.value)}
            rows={4}
            className="mt-2 w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
            placeholder="Example: Evidence points to a publication, not a company."
          />
        </label>
        {error ? (
          <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </p>
        ) : null}
        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={isSubmitting || reasonIsEmpty}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-red-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : null}
            Reject Candidate
          </button>
        </div>
      </section>
    </div>
  );
}

export function CompanyDiscoveryPage(): ReactElement {
  const [query, setQuery] = useState("AI startup food technology");
  const [sector, setSector] = useState("Food and Beverage");
  const [country, setCountry] = useState("Germany");
  const [limit, setLimit] = useState(10);
  const [searchResult, setSearchResult] =
    useState<CompanyDiscoverySearchResponse | null>(null);
  const [reviewMessage, setReviewMessage] = useState<ReviewMessage | null>(null);
  const [rejectTarget, setRejectTarget] = useState<ReviewTarget | null>(null);
  const [rejectError, setRejectError] = useState<string | null>(null);

  const pendingQuery = useQuery({
    queryKey: pendingDiscoveryQueryKey,
    queryFn: () => getPendingDiscoveryCandidates(50),
  });

  const refreshPending = async (): Promise<void> => {
    await pendingQuery.refetch();
  };

  const searchMutation = useMutation({
    mutationFn: searchDiscoveryCandidates,
    onSuccess: async (data) => {
      setSearchResult(data);
      setReviewMessage(null);
      await refreshPending();
    },
  });

  const approveMutation = useMutation({
    mutationFn: approveDiscoveryCandidate,
    onSuccess: async (data) => {
      setReviewMessage({
        tone: "success",
        text: `${data.company.vendor_name} approved and added to the trusted AtlasAI knowledge base. ${data.indexed_chunks.toLocaleString()} chunk${data.indexed_chunks === 1 ? "" : "s"} indexed. Indexing status: ${data.indexing_status}.`,
      });
      await refreshPending();
    },
    onError: (error) => {
      setReviewMessage({
        tone: "error",
        text: getErrorMessage(error, "Unable to approve this candidate."),
      });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({
      candidateId,
      rejectionReason,
    }: {
      candidateId: string;
      rejectionReason: string;
    }) => rejectDiscoveryCandidate(candidateId, rejectionReason),
    onSuccess: async (candidate) => {
      setRejectTarget(null);
      setRejectError(null);
      setReviewMessage({
        tone: "success",
        text: `${candidate.company_name} rejected and removed from pending review.`,
      });
      await refreshPending();
    },
    onError: (error) => {
      setRejectError(getErrorMessage(error, "Unable to reject this candidate."));
    },
  });

  const pendingCandidates = pendingQuery.data?.items ?? [];
  const displayedCandidates = useMemo(() => {
    const byId = new Map<string, CompanyDiscoveryCandidate>();
    for (const candidate of searchResult?.items ?? []) {
      byId.set(candidate.id, candidate);
    }
    for (const candidate of pendingCandidates) {
      byId.set(candidate.id, candidate);
    }
    return [...byId.values()];
  }, [pendingCandidates, searchResult?.items]);

  const searchError = searchMutation.isError
    ? getErrorMessage(searchMutation.error, "Unable to run discovery search.")
    : null;

  const handleSearch = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    searchMutation.mutate({
      query: query.trim() || null,
      sector: sector.trim() || null,
      country: country.trim() || null,
      limit,
    });
  };

  const handleApprove = (candidate: CompanyDiscoveryCandidate): void => {
    setReviewMessage(null);
    approveMutation.mutate(candidate.id);
  };

  const handleRejectStart = (candidate: CompanyDiscoveryCandidate): void => {
    setRejectError(null);
    setRejectTarget({ candidate, reason: "" });
  };

  const handleRejectSubmit = (): void => {
    if (!rejectTarget) {
      return;
    }
    const rejectionReason = rejectTarget.reason.trim();
    if (!rejectionReason) {
      setRejectError("A rejection reason is required.");
      return;
    }
    rejectMutation.mutate({
      candidateId: rejectTarget.candidate.id,
      rejectionReason,
    });
  };

  return (
    <PageContainer
      title="Company Discovery"
      subtitle="Discover and review external AI company candidates before adding them to the trusted AtlasAI knowledge base."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <form onSubmit={handleSearch} className="grid gap-4 lg:grid-cols-[1.4fr_1fr_1fr_8rem_auto] lg:items-end">
          <label>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Search Query
            </span>
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            />
          </label>
          <label>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Sector
            </span>
            <input
              type="text"
              value={sector}
              onChange={(event) => setSector(event.target.value)}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            />
          </label>
          <label>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Country
            </span>
            <input
              type="text"
              value={country}
              onChange={(event) => setCountry(event.target.value)}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            />
          </label>
          <label>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Result Limit
            </span>
            <input
              type="number"
              min={1}
              max={50}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
              className="mt-2 h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            />
          </label>
          <button
            type="submit"
            disabled={searchMutation.isPending}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            {searchMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Search className="h-4 w-4" aria-hidden="true" />
            )}
            Discover Companies
          </button>
        </form>

        {searchError ? (
          <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
            {searchError}
          </p>
        ) : null}

        {searchResult ? (
          <div className="mt-5 space-y-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <SummaryMetric label="Articles Fetched" value={searchResult.articles_fetched} />
              <SummaryMetric label="Candidates Extracted" value={searchResult.provider_candidates_extracted} />
              <SummaryMetric label="Candidates Created" value={searchResult.candidates_created} />
              <SummaryMetric label="Candidates Skipped" value={searchResult.candidates_skipped} />
            </div>
            {searchResult.items.length === 0 ? (
              <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
                No verified company candidates were discovered from the current search. Try adjusting the query or sector.
              </p>
            ) : null}
            {searchResult.provider_extraction_details.length > 0 ? (
              <details className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
                <summary className="cursor-pointer text-sm font-medium text-slate-700 dark:text-slate-200">
                  Diagnostics
                </summary>
                <div className="mt-3 max-h-56 space-y-2 overflow-auto">
                  {searchResult.provider_extraction_details.map((detail, index) => (
                    <div
                      key={`${detail.title ?? "untitled"}-${detail.extraction_skip_reason}-${index}`}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                    >
                      <span className="font-medium">{detail.extraction_skip_reason}</span>
                      <span> - {formatOptional(detail.source_domain)}</span>
                      <p className="mt-1">{formatOptional(detail.title)}</p>
                    </div>
                  ))}
                </div>
              </details>
            ) : null}
          </div>
        ) : null}
      </section>

      {reviewMessage ? (
        <section
          className={
            reviewMessage.tone === "success"
              ? "rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300"
              : "rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
          }
        >
          {reviewMessage.text}
        </section>
      ) : null}

      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-950 dark:text-white">
              Pending Review
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Review evidence before approving any candidate into trusted company data.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              void refreshPending();
            }}
            disabled={pendingQuery.isFetching}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <RefreshCcw
              className={pendingQuery.isFetching ? "h-4 w-4 animate-spin" : "h-4 w-4"}
              aria-hidden="true"
            />
            Refresh
          </button>
        </div>

        {pendingQuery.isLoading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
            Loading pending candidates...
          </div>
        ) : null}

        {pendingQuery.isError ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-5 dark:border-red-900/60 dark:bg-red-950/30">
            <p className="text-sm font-medium text-red-700 dark:text-red-300">
              Unable to load pending candidates.
            </p>
            <button
              type="button"
              onClick={() => {
                void refreshPending();
              }}
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
            >
              <RefreshCcw className="h-4 w-4" aria-hidden="true" />
              Retry
            </button>
          </div>
        ) : null}

        {!pendingQuery.isLoading && !pendingQuery.isError && displayedCandidates.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <ShieldCheck className="mx-auto h-6 w-6 text-slate-400" aria-hidden="true" />
            <h3 className="mt-3 text-base font-semibold text-slate-950 dark:text-white">
              No pending candidates
            </h3>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Run a discovery search to create candidates for review.
            </p>
          </div>
        ) : null}

        {displayedCandidates.length > 0 ? (
          <div className="grid gap-4">
            {displayedCandidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                isApproving={approveMutation.isPending}
                isRejecting={rejectMutation.isPending}
                onApprove={handleApprove}
                onReject={handleRejectStart}
              />
            ))}
          </div>
        ) : null}
      </section>

      {rejectTarget ? (
        <RejectDialog
          target={rejectTarget}
          error={rejectError}
          isSubmitting={rejectMutation.isPending}
          onCancel={() => {
            setRejectTarget(null);
            setRejectError(null);
          }}
          onReasonChange={(reason) => setRejectTarget({ ...rejectTarget, reason })}
          onSubmit={handleRejectSubmit}
        />
      ) : null}
    </PageContainer>
  );
}
