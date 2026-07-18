"""Company discovery endpoints for human-reviewed candidate approval."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_company_discovery_service
from app.schemas.discovery import (
    CompanyDiscoveryApprovalResponse,
    CompanyDiscoveryCandidateResponse,
    CompanyDiscoveryListResponse,
    CompanyDiscoveryRejectionRequest,
    CompanyDiscoveryRequest,
    CompanyDiscoverySummary,
)
from app.services.company_discovery_service import (
    CandidateReviewStateError,
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderConfigurationError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderRequestError,
    DiscoveryProviderResponseError,
    DuplicateCompanyError,
)

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.post("/search", response_model=CompanyDiscoverySummary)
async def search_discovery_candidates(
    request: CompanyDiscoveryRequest,
    discovery_service=Depends(get_company_discovery_service),
) -> CompanyDiscoverySummary:
    """Trigger external company discovery and create pending candidates."""

    try:
        summary = discovery_service.discover_candidates(
            query=request.query,
            sector=request.sector,
            country=request.country,
            limit=request.limit,
        )
    except DiscoveryProviderConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except DiscoveryProviderAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except DiscoveryProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except (DiscoveryProviderRequestError, DiscoveryProviderResponseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return CompanyDiscoverySummary(
        candidates_found=summary.candidates_found,
        candidates_created=summary.candidates_created,
        candidates_skipped=summary.candidates_skipped,
        articles_fetched=summary.articles_fetched,
        provider_candidates_extracted=summary.provider_candidates_extracted,
        provider_extraction_skipped=summary.provider_extraction_skipped,
        items=summary.items,
        skipped=summary.skipped,
        provider_extraction_details=summary.provider_extraction_details,
    )


@router.get("/pending", response_model=CompanyDiscoveryListResponse)
async def list_pending_discovery_candidates(
    limit: int = 50,
    discovery_service=Depends(get_company_discovery_service),
) -> CompanyDiscoveryListResponse:
    """List pending candidates awaiting human review."""

    candidates = discovery_service.list_pending(limit=limit)
    return CompanyDiscoveryListResponse(items=candidates, total=len(candidates))


@router.get("/{candidate_id}", response_model=CompanyDiscoveryCandidateResponse)
async def get_discovery_candidate(
    candidate_id: UUID,
    discovery_service=Depends(get_company_discovery_service),
) -> CompanyDiscoveryCandidateResponse:
    """Fetch a discovery candidate and its evidence."""

    candidate = discovery_service.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discovery candidate not found")
    return candidate


@router.post("/{candidate_id}/approve", response_model=CompanyDiscoveryApprovalResponse)
async def approve_discovery_candidate(
    candidate_id: UUID,
    discovery_service=Depends(get_company_discovery_service),
) -> CompanyDiscoveryApprovalResponse:
    """Approve a pending candidate and add it to trusted company data."""

    try:
        company, indexing_status, indexed_chunks = discovery_service.approve_candidate(candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateReviewStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DuplicateCompanyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return CompanyDiscoveryApprovalResponse(
        company=company,
        indexing_status=indexing_status,
        indexed_chunks=indexed_chunks,
    )


@router.post("/{candidate_id}/reject", response_model=CompanyDiscoveryCandidateResponse)
async def reject_discovery_candidate(
    candidate_id: UUID,
    request: CompanyDiscoveryRejectionRequest | None = None,
    discovery_service=Depends(get_company_discovery_service),
) -> CompanyDiscoveryCandidateResponse:
    """Reject a pending candidate without adding it to trusted data."""

    try:
        return discovery_service.reject_candidate(
            candidate_id,
            rejection_reason=request.rejection_reason if request else None,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateReviewStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
