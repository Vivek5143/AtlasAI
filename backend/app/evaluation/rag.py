"""Deterministic RAG evaluation utilities for AtlasAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from app.ai import RetrievedChunk


UNKNOWN_INDICATORS = (
    "not enough information",
    "does not contain enough information",
    "cannot determine",
    "not available in the provided data",
    "insufficient information",
    "available data does not",
)


@dataclass(slots=True, frozen=True)
class RAGEvaluationCase:
    """One representative RAG evaluation case."""

    id: str
    category: str
    question: str
    expected_source_types: list[str] = field(default_factory=list)
    expected_entities: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)
    should_answer: bool = True
    expected_min_sources: int = 1
    optional: bool = False
    skip_if_entity_absent: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RAGEvaluationCase":
        """Build a case from JSON data."""

        return cls(
            id=str(payload["id"]),
            category=str(payload["category"]),
            question=str(payload["question"]),
            expected_source_types=list(payload.get("expected_source_types", [])),
            expected_entities=list(payload.get("expected_entities", [])),
            expected_keywords=list(payload.get("expected_keywords", [])),
            forbidden_keywords=list(payload.get("forbidden_keywords", [])),
            should_answer=bool(payload.get("should_answer", True)),
            expected_min_sources=int(payload.get("expected_min_sources", 1)),
            optional=bool(payload.get("optional", False)),
            skip_if_entity_absent=payload.get("skip_if_entity_absent"),
            notes=payload.get("notes"),
        )


@dataclass(slots=True)
class RAGEvaluationResult:
    """Evaluation result for one case."""

    case_id: str
    category: str
    question: str
    status: str
    passed: bool
    skipped: bool
    reasons: list[str]
    retrieved_count: int
    top_k_scores: list[float]
    retrieved_source_types: list[str]
    retrieved_titles: list[str]
    expected_entities_found: list[str]
    expected_entities_missing: list[str]
    entity_coverage: float
    expected_source_type_found: bool
    citation_count: int
    answer: str | None = None


@dataclass(slots=True)
class RAGEvaluationSummary:
    """Aggregate evaluation metrics."""

    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    overall_pass_rate: float
    hit_at_k: float
    source_type_accuracy: float
    entity_coverage: float
    grounded_answer_rate: float
    unknown_refusal_accuracy: float
    citation_presence: float
    category_metrics: dict[str, dict[str, int]]
    results: list[RAGEvaluationResult]


def load_cases(path: Path) -> list[RAGEvaluationCase]:
    """Load JSON or JSONL RAG evaluation cases."""

    if path.suffix.lower() == ".jsonl":
        return [
            RAGEvaluationCase.from_dict(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("cases", [])
    return [RAGEvaluationCase.from_dict(item) for item in payload]


def chunk_search_text(chunk: RetrievedChunk) -> str:
    """Return normalized searchable text for a retrieved chunk."""

    metadata = chunk.metadata or {}
    values = [
        chunk.page_content,
        str(metadata.get("title") or ""),
        str(metadata.get("source") or ""),
        str(metadata.get("entity_type") or ""),
    ]
    return "\n".join(values).lower()


def contains_term(text: str, term: str) -> bool:
    """Return whether text contains a term with case-insensitive matching."""

    normalized_term = term.strip().lower()
    if not normalized_term:
        return False
    return re.search(rf"\b{re.escape(normalized_term)}\b", text, re.IGNORECASE) is not None


def find_expected_entities(
    chunks: list[RetrievedChunk],
    expected_entities: list[str],
) -> tuple[list[str], list[str], float]:
    """Find expected entities in retrieved chunks and compute coverage."""

    if not expected_entities:
        return [], [], 1.0

    searchable = "\n".join(chunk_search_text(chunk) for chunk in chunks)
    found = [entity for entity in expected_entities if contains_term(searchable, entity)]
    missing = [entity for entity in expected_entities if entity not in found]
    return found, missing, len(found) / len(expected_entities)


def source_type_found(
    chunks: list[RetrievedChunk],
    expected_source_types: list[str],
) -> bool:
    """Return whether any expected source type appears in retrieved metadata."""

    if not expected_source_types:
        return True
    actual_types = {
        str((chunk.metadata or {}).get("entity_type") or "").lower()
        for chunk in chunks
    }
    return any(source_type.lower() in actual_types for source_type in expected_source_types)


def answer_indicates_unknown(answer: str | None) -> bool:
    """Return whether an answer expresses grounded uncertainty."""

    if not answer:
        return False
    normalized = answer.lower()
    return any(indicator in normalized for indicator in UNKNOWN_INDICATORS)


def citations_are_present(citations: list[str], chunks: list[RetrievedChunk]) -> bool:
    """Return whether citations exist and point to non-empty retrieved metadata."""

    if not chunks:
        return False
    if not citations:
        return False
    if len(citations) > len(chunks):
        return False
    for index, citation in enumerate(citations, start=1):
        if f"[{index}]" not in citation:
            return False
        metadata = chunks[index - 1].metadata or {}
        if not (metadata.get("title") or metadata.get("source")):
            return False
    return True


def evaluate_case(
    case: RAGEvaluationCase,
    chunks: list[RetrievedChunk],
    *,
    answer: str | None = None,
    citations: list[str] | None = None,
    skipped_reason: str | None = None,
) -> RAGEvaluationResult:
    """Apply deterministic checks to one evaluation case."""

    if skipped_reason:
        return RAGEvaluationResult(
            case_id=case.id,
            category=case.category,
            question=case.question,
            status="skipped",
            passed=False,
            skipped=True,
            reasons=[skipped_reason],
            retrieved_count=0,
            top_k_scores=[],
            retrieved_source_types=[],
            retrieved_titles=[],
            expected_entities_found=[],
            expected_entities_missing=list(case.expected_entities),
            entity_coverage=0.0,
            expected_source_type_found=False,
            citation_count=0,
            answer=answer,
        )

    citations = citations or []
    reasons: list[str] = []
    found_entities, missing_entities, entity_coverage = find_expected_entities(
        chunks,
        case.expected_entities,
    )
    has_expected_source_type = source_type_found(chunks, case.expected_source_types)
    searchable = "\n".join(chunk_search_text(chunk) for chunk in chunks)
    retrieved_source_types = [
        str((chunk.metadata or {}).get("entity_type") or "unknown")
        for chunk in chunks
    ]
    retrieved_titles = [
        str((chunk.metadata or {}).get("title") or "Untitled")
        for chunk in chunks
    ]

    if case.should_answer:
        if len(chunks) < case.expected_min_sources:
            reasons.append(
                f"Expected at least {case.expected_min_sources} retrieved source(s), got {len(chunks)}."
            )
        if case.expected_entities and missing_entities:
            reasons.append(
                "Missing expected entities in top-k: "
                + ", ".join(f'"{entity}"' for entity in missing_entities)
            )
        if case.expected_source_types and not has_expected_source_type:
            reasons.append(
                "Missing expected source type(s): "
                + ", ".join(case.expected_source_types)
            )
        for keyword in case.expected_keywords:
            if not contains_term(searchable, keyword) and not contains_term(answer or "", keyword):
                reasons.append(f'Expected keyword "{keyword}" was not found.')
        for keyword in case.forbidden_keywords:
            if contains_term(searchable, keyword) or contains_term(answer or "", keyword):
                reasons.append(f'Forbidden keyword "{keyword}" was found.')
        if answer is not None and chunks and not citations_are_present(citations, chunks):
            reasons.append("Expected citations for retrieved answer context.")
    else:
        if answer is not None and not answer_indicates_unknown(answer):
            reasons.append("Expected an insufficient-information answer.")
        if answer is None and chunks:
            reasons.append("Out-of-scope retrieval returned context in retrieval-only mode.")

    passed = not reasons
    return RAGEvaluationResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        status="passed" if passed else "failed",
        passed=passed,
        skipped=False,
        reasons=reasons,
        retrieved_count=len(chunks),
        top_k_scores=[float(chunk.score) for chunk in chunks],
        retrieved_source_types=retrieved_source_types,
        retrieved_titles=retrieved_titles,
        expected_entities_found=found_entities,
        expected_entities_missing=missing_entities,
        entity_coverage=round(entity_coverage, 4),
        expected_source_type_found=has_expected_source_type,
        citation_count=len(citations),
        answer=answer,
    )


def _percent(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def summarize_results(results: list[RAGEvaluationResult]) -> RAGEvaluationSummary:
    """Aggregate individual evaluation results."""

    total = len(results)
    passed = sum(1 for result in results if result.passed)
    skipped = sum(1 for result in results if result.skipped)
    failed = total - passed - skipped
    active_results = [result for result in results if not result.skipped]
    answerable_results = [result for result in active_results if result.retrieved_count > 0]
    unknown_results = [
        result
        for result in active_results
        if result.answer is not None and result.retrieved_count == 0
    ]

    entity_cases = [
        result
        for result in active_results
        if result.expected_entities_found or result.expected_entities_missing
    ]
    source_type_cases = [
        result
        for result in active_results
        if result.expected_source_type_found or result.retrieved_source_types
    ]
    citation_cases = [
        result
        for result in active_results
        if result.answer is not None and result.retrieved_count > 0
    ]

    category_metrics: dict[str, dict[str, int]] = {}
    for result in results:
        metrics = category_metrics.setdefault(
            result.category,
            {"passed": 0, "failed": 0, "skipped": 0, "total": 0},
        )
        metrics["total"] += 1
        if result.skipped:
            metrics["skipped"] += 1
        elif result.passed:
            metrics["passed"] += 1
        else:
            metrics["failed"] += 1

    return RAGEvaluationSummary(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_tests=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        overall_pass_rate=_percent(passed, total - skipped),
        hit_at_k=_percent(
            sum(1 for result in entity_cases if result.expected_entities_found),
            len(entity_cases),
        ),
        source_type_accuracy=_percent(
            sum(1 for result in source_type_cases if result.expected_source_type_found),
            len(source_type_cases),
        ),
        entity_coverage=round(
            sum(result.entity_coverage for result in entity_cases) / len(entity_cases) * 100,
            1,
        )
        if entity_cases
        else 0.0,
        grounded_answer_rate=_percent(
            sum(1 for result in answerable_results if result.passed),
            len(answerable_results),
        ),
        unknown_refusal_accuracy=_percent(
            sum(1 for result in unknown_results if result.passed),
            len(unknown_results),
        ),
        citation_presence=_percent(
            sum(1 for result in citation_cases if result.citation_count > 0),
            len(citation_cases),
        ),
        category_metrics=category_metrics,
        results=results,
    )


def summary_to_dict(summary: RAGEvaluationSummary) -> dict[str, Any]:
    """Serialize an evaluation summary."""

    return {
        "timestamp": summary.timestamp,
        "total_tests": summary.total_tests,
        "passed": summary.passed,
        "failed": summary.failed,
        "skipped": summary.skipped,
        "overall_pass_rate": summary.overall_pass_rate,
        "retrieval_metrics": {
            "hit_at_k": summary.hit_at_k,
            "source_type_accuracy": summary.source_type_accuracy,
            "entity_coverage": summary.entity_coverage,
        },
        "behavior_metrics": {
            "grounded_answer_rate": summary.grounded_answer_rate,
            "unknown_refusal_accuracy": summary.unknown_refusal_accuracy,
            "citation_presence": summary.citation_presence,
        },
        "category_metrics": summary.category_metrics,
        "results": [
            {
                "case_id": result.case_id,
                "category": result.category,
                "question": result.question,
                "status": result.status,
                "passed": result.passed,
                "skipped": result.skipped,
                "reasons": result.reasons,
                "retrieved_count": result.retrieved_count,
                "top_k_scores": result.top_k_scores,
                "retrieved_source_types": result.retrieved_source_types,
                "retrieved_titles": result.retrieved_titles,
                "expected_entities_found": result.expected_entities_found,
                "expected_entities_missing": result.expected_entities_missing,
                "entity_coverage": result.entity_coverage,
                "expected_source_type_found": result.expected_source_type_found,
                "citation_count": result.citation_count,
                "answer": result.answer,
            }
            for result in summary.results
        ],
    }
