"""Sector endpoints.

Provides read-only APIs for listing and fetching sectors.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_sector_service
from app.schemas.sector import SectorListResponse, SectorResponse

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("", response_model=SectorListResponse)
async def list_sectors(
    sector_service=Depends(get_sector_service),
) -> SectorListResponse:

    """List all sectors."""


    sectors = sector_service.get_all_sectors()
    return SectorListResponse(items=sectors, total=len(sectors))


@router.get("/{sector_id}", response_model=SectorResponse)
async def get_sector(
    sector_id: UUID,
    sector_service=Depends(get_sector_service),
) -> SectorResponse:
    """Fetch a sector by id."""

    sector = sector_service.get_sector(sector_id)
    if sector is None:
        raise HTTPException(status_code=404, detail="Sector not found")
    return sector

