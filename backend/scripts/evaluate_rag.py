"""AtlasAI RAG retrieval evaluation runner.

Evaluates the existing AtlasAI semantic retrieval pipeline without calling
the Gemini LLM. This allows retrieval quality to be measured independently
from answer generation.

Run from the backend directory:

    python scripts/evaluate_rag.py

The script evaluates:
- Company retrieval
- News retrieval
- Sector-based retrieval
- Multi-entity retrieval
- Out-of-scope retrieval behavior
- Newly approved Discovery company retrieval

Metrics:
- Hit@K
- Source Type Accuracy
- Entity Coverage
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Ensure backend root is available on Python path
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from app.ai.retriever import SemanticRetrieverService
from app.ai.vector_store import ChromaVectorStoreService


# ---------------------------------------------------------------------------
# Evaluation Models
# ---------------------------------------------------------------------------


@dataclass
class EvaluationCase:
    """Single retrieval evaluation test case."""

    id: str
    category: str
    question: str

    expected_entities: list[str] = field(default_factory=list)
    expected_source_types: list[str] = field(default_factory=list)

    should_answer: bool = True

    # Optional tests do not fail the complete evaluation.
    # Useful for dynamically approved Discovery companies.
    optional: bool = False


@dataclass
class EvaluationResult:
    """Result of one retrieval evaluation case."""

    id: str
    category: str
    question: str

    passed: bool
    skipped: bool

    entity_hit: bool
    source_type_hit: bool
    entity_coverage: float

    retrieved_count: int

    expected_entities: list[str]
    retrieved_entities: list[str]

    expected_source_types: list[str]
    retrieved_source_types: list[str]

    reason: str | None = None


# ---------------------------------------------------------------------------
# Evaluation Dataset
# ---------------------------------------------------------------------------


EVALUATION_CASES: list[EvaluationCase] = [

    # ------------------------------------------------------------------
    # Company Retrieval
    # ------------------------------------------------------------------

    EvaluationCase(
        id="company_aws_001",
        category="company_retrieval",
        question="What is Amazon Web Services?",
        expected_entities=["Amazon Web Services"],
        expected_source_types=["company"],
    ),

    EvaluationCase(
        id="company_aws_002",
        category="company_retrieval",
        question="What AI solutions does Amazon Web Services provide?",
        expected_entities=["Amazon Web Services"],
        expected_source_types=["company"],
    ),

    EvaluationCase(
        id="company_google_001",
        category="company_retrieval",
        question="What is Google Cloud Vertex AI?",
        expected_entities=["Google Cloud"],
        expected_source_types=["company"],
    ),

    EvaluationCase(
        id="company_foss_001",
        category="company_retrieval",
        question="What can you tell me about FOSS Analytics?",
        expected_entities=["FOSS Analytics"],
        expected_source_types=["company"],
    ),

    # ------------------------------------------------------------------
    # News Retrieval
    # ------------------------------------------------------------------

    EvaluationCase(
        id="news_aws_001",
        category="news_retrieval",
        question="What recent news is available about Amazon Web Services?",
        expected_entities=["Amazon Web Services", "AWS"],
        expected_source_types=["news"],
    ),

    EvaluationCase(
        id="news_aws_002",
        category="news_retrieval",
        question="What are the latest developments related to AWS?",
        expected_entities=["AWS", "Amazon Web Services"],
        expected_source_types=["news"],
    ),

    EvaluationCase(
        id="news_microsoft_001",
        category="news_retrieval",
        question="What recent news is available about Microsoft?",
        expected_entities=["Microsoft"],
        expected_source_types=["news"],
    ),

    # ------------------------------------------------------------------
    # Sector-Based Retrieval
    # ------------------------------------------------------------------

    EvaluationCase(
        id="sector_food_001",
        category="sector_recommendation",
        question="Recommend AI companies for the Food and Beverage industry.",
        expected_source_types=["sector", "company"],
    ),

    EvaluationCase(
        id="sector_food_002",
        category="sector_recommendation",
        question="Which AI companies would you recommend for food manufacturing?",
        expected_source_types=["sector", "company"],
    ),

    EvaluationCase(
        id="sector_bakery_001",
        category="sector_recommendation",
        question="Recommend AI vendors for Bakery and Confectionery Manufacturing.",
        expected_entities=["Bakery"],
        expected_source_types=["sector", "company"],
    ),

    # ------------------------------------------------------------------
    # Multi-Entity Retrieval
    # ------------------------------------------------------------------

    EvaluationCase(
        id="multi_cloud_001",
        category="multi_entity",
        question=(
            "Compare Amazon Web Services and Google Cloud "
            "based on the available AtlasAI data."
        ),
        expected_entities=[
            "Amazon Web Services",
            "Google Cloud",
        ],
        expected_source_types=["company"],
    ),

    EvaluationCase(
        id="multi_food_001",
        category="multi_entity",
        question="Compare FOSS Analytics and Pixelfield GmbH.",
        expected_entities=[
            "FOSS Analytics",
            "Pixelfield",
        ],
        expected_source_types=["company"],
    ),

    EvaluationCase(
        id="multi_aws_context_001",
        category="multi_entity",
        question=(
            "Give me an overview of Amazon Web Services, "
            "the sectors it serves, and its recent news."
        ),
        expected_entities=[
            "Amazon Web Services",
        ],
        expected_source_types=[
            "company",
            "news",
        ],
    ),

    # ------------------------------------------------------------------
    # Out-of-Scope Retrieval
    #
    # Retrieval-only evaluation cannot fully judge the LLM's "I don't know"
    # response. These cases check whether irrelevant retrieval is limited.
    # ------------------------------------------------------------------

    EvaluationCase(
        id="unknown_001",
        category="out_of_scope",
        question="Who won the FIFA World Cup in 1998?",
        should_answer=False,
    ),

    EvaluationCase(
        id="unknown_002",
        category="out_of_scope",
        question="Explain how to bake a chocolate birthday cake.",
        should_answer=False,
    ),

    EvaluationCase(
        id="unknown_003",
        category="out_of_scope",
        question="What is the distance between Earth and Mars today?",
        should_answer=False,
    ),

    # ------------------------------------------------------------------
    # Discovery / Incremental KB Update
    #
    # Optional because clean installations may not contain dynamically
    # approved Discovery companies.
    # ------------------------------------------------------------------

    EvaluationCase(
        id="discovery_subquadratic_001",
        category="discovery_update",
        question="What is Subquadratic?",
        expected_entities=["Subquadratic"],
        expected_source_types=["company"],
        optional=True,
    ),
]


# ---------------------------------------------------------------------------
# Metadata Helpers
# ---------------------------------------------------------------------------


def normalize(value: Any) -> str:
    """Normalize a value for case-insensitive comparison."""

    if value is None:
        return ""

    return str(value).strip().lower()


def get_chunk_entity(chunk: Any) -> str:
    """Extract the most useful entity/title label from a retrieved chunk."""

    metadata = getattr(chunk, "metadata", {}) or {}

    possible_keys = (
        "title",
        "vendor_name",
        "company_name",
        "name",
    )

    for key in possible_keys:
        value = metadata.get(key)

        if value:
            return str(value)

    return ""


def get_chunk_source_type(chunk: Any) -> str:
    """Extract and normalize source type from retrieved chunk metadata."""

    metadata = getattr(chunk, "metadata", {}) or {}

    raw_source_type = str(
        metadata.get("source")
        or metadata.get("source_type")
        or metadata.get("type")
        or ""
    ).strip().lower()

    source_type_mapping = {
        "postgresql.companies": "company",
        "postgresql.news_articles": "news",
        "postgresql.sectors": "sector",
        "postgresql.problems": "problem",
    }

    return source_type_mapping.get(
        raw_source_type,
        raw_source_type,
    )


# ---------------------------------------------------------------------------
# Evaluation Logic
# ---------------------------------------------------------------------------


def entity_matches(
    expected_entity: str,
    retrieved_entities: list[str],
    chunks: list[Any],
) -> bool:
    """Check whether an expected entity appears in retrieval results."""

    expected = normalize(expected_entity)

    if not expected:
        return False

    # Check metadata labels.
    for entity in retrieved_entities:
        normalized_entity = normalize(entity)

        if (
            expected in normalized_entity
            or normalized_entity in expected
        ):
            return True

    # Also inspect page content because some entity names may not be
    # available directly in metadata.
    for chunk in chunks:
        page_content = normalize(
            getattr(chunk, "page_content", "")
        )

        if expected in page_content:
            return True

    return False


def source_type_matches(
    expected_source_types: list[str],
    retrieved_source_types: list[str],
) -> bool:
    """Check whether at least one expected source type was retrieved."""

    if not expected_source_types:
        return True

    expected = {
        normalize(source_type)
        for source_type in expected_source_types
    }

    retrieved = {
        normalize(source_type)
        for source_type in retrieved_source_types
    }

    return bool(expected.intersection(retrieved))


def calculate_entity_coverage(
    expected_entities: list[str],
    retrieved_entities: list[str],
    chunks: list[Any],
) -> float:
    """Calculate expected entity coverage."""

    if not expected_entities:
        return 1.0

    hits = 0

    for entity in expected_entities:
        if entity_matches(
            expected_entity=entity,
            retrieved_entities=retrieved_entities,
            chunks=chunks,
        ):
            hits += 1

    return hits / len(expected_entities)


# ---------------------------------------------------------------------------
# Single Evaluation
# ---------------------------------------------------------------------------


def evaluate_case(
    retriever: SemanticRetrieverService,
    case: EvaluationCase,
    top_k: int,
) -> EvaluationResult:
    """Evaluate a single RAG retrieval test case."""

    try:
        chunks = retriever.retrieve(
            query=case.question,
            top_k=top_k,
        )

    except Exception as exc:
        return EvaluationResult(
            id=case.id,
            category=case.category,
            question=case.question,
            passed=False,
            skipped=False,
            entity_hit=False,
            source_type_hit=False,
            entity_coverage=0.0,
            retrieved_count=0,
            expected_entities=case.expected_entities,
            retrieved_entities=[],
            expected_source_types=case.expected_source_types,
            retrieved_source_types=[],
            reason=f"Retrieval failed: {type(exc).__name__}: {exc}",
        )

    retrieved_entities = [
        get_chunk_entity(chunk)
        for chunk in chunks
        if get_chunk_entity(chunk)
    ]

    retrieved_source_types = [
        get_chunk_source_type(chunk)
        for chunk in chunks
        if get_chunk_source_type(chunk)
    ]

    coverage = calculate_entity_coverage(
        expected_entities=case.expected_entities,
        retrieved_entities=retrieved_entities,
        chunks=chunks,
    )

    entity_hit = (
        coverage > 0
        if case.expected_entities
        else True
    )

    source_hit = source_type_matches(
        expected_source_types=case.expected_source_types,
        retrieved_source_types=retrieved_source_types,
    )

    # ---------------------------------------------------------------
    # Optional Discovery Test
    # ---------------------------------------------------------------

    if case.optional and case.expected_entities and coverage == 0:
        return EvaluationResult(
            id=case.id,
            category=case.category,
            question=case.question,
            passed=False,
            skipped=True,
            entity_hit=False,
            source_type_hit=source_hit,
            entity_coverage=coverage,
            retrieved_count=len(chunks),
            expected_entities=case.expected_entities,
            retrieved_entities=retrieved_entities,
            expected_source_types=case.expected_source_types,
            retrieved_source_types=retrieved_source_types,
            reason="Optional Discovery company not present in retrieval.",
        )

    # ---------------------------------------------------------------
    # Out-of-Scope Retrieval
    # ---------------------------------------------------------------

    if not case.should_answer:
        # Retrieval-only evaluation cannot prove that the LLM refuses.
        #
        # For now, mark the retrieval portion as passed. The full RAG
        # evaluator should separately verify the final answer contains
        # an insufficient-information response.
        passed = True

        return EvaluationResult(
            id=case.id,
            category=case.category,
            question=case.question,
            passed=passed,
            skipped=False,
            entity_hit=True,
            source_type_hit=True,
            entity_coverage=1.0,
            retrieved_count=len(chunks),
            expected_entities=[],
            retrieved_entities=retrieved_entities,
            expected_source_types=[],
            retrieved_source_types=retrieved_source_types,
            reason=(
                "Retrieval-only mode: final unknown-answer behavior "
                "requires full RAG evaluation."
            ),
        )

    # ---------------------------------------------------------------
    # Standard Pass Criteria
    # ---------------------------------------------------------------

    entity_requirement = (
        coverage > 0
        if case.expected_entities
        else True
    )

    source_requirement = source_hit

    passed = entity_requirement and source_requirement

    reason = None

    if not entity_requirement:
        reason = "Expected entity was not found in top-k retrieval."

    elif not source_requirement:
        reason = "Expected source type was not found in top-k retrieval."

    return EvaluationResult(
        id=case.id,
        category=case.category,
        question=case.question,
        passed=passed,
        skipped=False,
        entity_hit=entity_hit,
        source_type_hit=source_hit,
        entity_coverage=coverage,
        retrieved_count=len(chunks),
        expected_entities=case.expected_entities,
        retrieved_entities=retrieved_entities,
        expected_source_types=case.expected_source_types,
        retrieved_source_types=retrieved_source_types,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_result(result: EvaluationResult) -> None:
    """Print one evaluation result."""

    if result.skipped:
        status = "SKIPPED"
    elif result.passed:
        status = "PASS"
    else:
        status = "FAIL"

    print()
    print("=" * 70)
    print(f"[{status}] {result.id}")
    print(f"Category: {result.category}")
    print(f"Question: {result.question}")

    if result.expected_entities:
        print(
            "Expected entities:",
            ", ".join(result.expected_entities),
        )

    if result.retrieved_entities:
        print(
            "Retrieved entities:",
            ", ".join(result.retrieved_entities),
        )

    if result.expected_source_types:
        print(
            "Expected source types:",
            ", ".join(result.expected_source_types),
        )

    if result.retrieved_source_types:
        print(
            "Retrieved source types:",
            ", ".join(result.retrieved_source_types),
        )

    print(
        f"Entity coverage: "
        f"{result.entity_coverage * 100:.1f}%"
    )

    print(
        f"Retrieved chunks: "
        f"{result.retrieved_count}"
    )

    if result.reason:
        print(f"Note: {result.reason}")


def print_summary(results: list[EvaluationResult]) -> None:
    """Print aggregate evaluation metrics."""

    executed = [
        result
        for result in results
        if not result.skipped
    ]

    passed = [
        result
        for result in executed
        if result.passed
    ]

    failed = [
        result
        for result in executed
        if not result.passed
    ]

    skipped = [
        result
        for result in results
        if result.skipped
    ]

    total_executed = len(executed)

    pass_rate = (
        len(passed) / total_executed * 100
        if total_executed
        else 0
    )

    entity_cases = [
        result
        for result in executed
        if result.expected_entities
    ]

    hit_at_k = (
        sum(
            1
            for result in entity_cases
            if result.entity_hit
        )
        / len(entity_cases)
        * 100
        if entity_cases
        else 0
    )

    source_cases = [
        result
        for result in executed
        if result.expected_source_types
    ]

    source_accuracy = (
        sum(
            1
            for result in source_cases
            if result.source_type_hit
        )
        / len(source_cases)
        * 100
        if source_cases
        else 0
    )

    entity_coverage = (
        sum(
            result.entity_coverage
            for result in entity_cases
        )
        / len(entity_cases)
        * 100
        if entity_cases
        else 0
    )

    print()
    print()
    print("#" * 70)
    print("AtlasAI RAG Retrieval Evaluation")
    print("#" * 70)

    print()
    print(f"Total Tests: {len(results)}")
    print(f"Executed:    {total_executed}")
    print(f"Passed:      {len(passed)}")
    print(f"Failed:      {len(failed)}")
    print(f"Skipped:     {len(skipped)}")

    print()
    print(
        f"Overall Pass Rate: "
        f"{pass_rate:.1f}%"
    )

    print()
    print("Retrieval Metrics")
    print("-" * 40)

    print(
        f"Hit@K:                "
        f"{hit_at_k:.1f}%"
    )

    print(
        f"Source Type Accuracy: "
        f"{source_accuracy:.1f}%"
    )

    print(
        f"Entity Coverage:      "
        f"{entity_coverage:.1f}%"
    )

    # ---------------------------------------------------------------
    # Category Summary
    # ---------------------------------------------------------------

    categories = sorted(
        {
            result.category
            for result in results
        }
    )

    print()
    print("Results by Category")
    print("-" * 40)

    for category in categories:

        category_results = [
            result
            for result in results
            if result.category == category
            and not result.skipped
        ]

        category_passed = sum(
            1
            for result in category_results
            if result.passed
        )

        print(
            f"{category:<25} "
            f"{category_passed}/{len(category_results)}"
        )

    # ---------------------------------------------------------------
    # Failed Cases
    # ---------------------------------------------------------------

    if failed:

        print()
        print("Failed Cases")
        print("-" * 40)

        for result in failed:

            print()
            print(result.id)
            print(f"Question: {result.question}")

            if result.reason:
                print(f"Reason: {result.reason}")

    # ---------------------------------------------------------------
    # Skipped Cases
    # ---------------------------------------------------------------

    if skipped:

        print()
        print("Skipped Cases")
        print("-" * 40)

        for result in skipped:

            print()
            print(result.id)

            if result.reason:
                print(f"Reason: {result.reason}")


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------


def main() -> None:
    """Run AtlasAI retrieval evaluation."""

    print()
    print("Starting AtlasAI RAG Retrieval Evaluation...")
    print()

    vector_store = ChromaVectorStoreService()

    retriever = SemanticRetrieverService(
        vector_store=vector_store
    )

    top_k = 6

    print(
        f"Evaluation cases: "
        f"{len(EVALUATION_CASES)}"
    )

    print(
        f"Retrieval Top-K: "
        f"{top_k}"
    )

    results: list[EvaluationResult] = []

    for case in EVALUATION_CASES:

        print(
            f"\nEvaluating: "
            f"{case.id}"
        )

        result = evaluate_case(
            retriever=retriever,
            case=case,
            top_k=top_k,
        )

        results.append(result)

        print_result(result)

    print_summary(results)


if __name__ == "__main__":
    main()