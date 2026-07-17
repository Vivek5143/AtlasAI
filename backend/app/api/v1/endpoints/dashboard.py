"""Dashboard endpoints.

Provides read-only APIs for dashboard metrics.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import (
    get_company_service,
    get_news_service,
    get_problem_service,
    get_sector_service,
)
from app.schemas.dashboard import DashboardListResponse, DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardListResponse)
async def get_dashboard(
    company_service=Depends(get_company_service),
    sector_service=Depends(get_sector_service),
    problem_service=Depends(get_problem_service),
    news_service=Depends(get_news_service),
) -> DashboardListResponse:
    """Return dashboard metrics."""

    company_stats = company_service.company_statistics()
    sector_stats = sector_service.sector_statistics()
    problem_stats = problem_service.problem_statistics()
    news_total = news_service.news_statistics()

    payload = DashboardResponse(
        total_companies=company_stats["total_companies"],
        total_sectors=sector_stats["total_sectors"],
        total_problems=problem_stats["total_problems"],
        total_news_articles=news_total["total_news_articles"],
        companies_with_sectors=company_stats["companies_with_sectors"],
        companies_with_news=company_stats["companies_with_news"],

        sectors_with_companies=sector_stats["sectors_with_companies"],
        problems_with_category=problem_stats["problems_with_category"],
        problems_with_severity=problem_stats["problems_with_severity"],
        generated_at=datetime.now(timezone.utc),
    )

    return DashboardListResponse(items=[payload], total=1)


@router.get("/stats", response_model=DashboardListResponse)
async def get_dashboard_stats(
    company_service=Depends(get_company_service),
    sector_service=Depends(get_sector_service),
    problem_service=Depends(get_problem_service),
    news_service=Depends(get_news_service),
) -> DashboardListResponse:
    """Return dashboard metrics (alias for /dashboard)."""

    # Reuse the primary payload to keep behavior consistent.
    return await get_dashboard(
        company_service=company_service,
        sector_service=sector_service,
        problem_service=problem_service,
        news_service=news_service,
    )







