"""Company endpoints.

Provides read-only APIs for listing, fetching, and searching companies.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_company_service
from app.schemas.company import CompanyListResponse, CompanyResponse



router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    company_service=Depends(get_company_service),
) -> CompanyListResponse:
    """List all companies."""

    companies = company_service.get_all_companies()
    return CompanyListResponse(items=companies, total=len(companies))


@router.get("/search", response_model=CompanyListResponse)
async def search_companies(
    keyword: str,
    company_service=Depends(get_company_service),
) -> CompanyListResponse:
    """Search companies by keyword."""

    companies = company_service.search_companies(keyword)
    return CompanyListResponse(items=companies, total=len(companies))


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    company_service=Depends(get_company_service),
) -> CompanyResponse:
    """Fetch a company by id."""

    company = company_service.get_company(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

