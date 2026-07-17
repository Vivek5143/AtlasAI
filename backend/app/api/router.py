"""Central API router registration for the AtlasAI backend."""

from fastapi import APIRouter

from app.api.v1.endpoints.ask import router as ask_router
from app.api.v1.endpoints.companies import router as companies_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.news import router as news_router
from app.api.v1.endpoints.problems import router as problems_router
from app.api.v1.endpoints.sectors import router as sectors_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(companies_router)
api_router.include_router(sectors_router)
api_router.include_router(problems_router)
api_router.include_router(news_router)
api_router.include_router(dashboard_router)
api_router.include_router(ask_router)
