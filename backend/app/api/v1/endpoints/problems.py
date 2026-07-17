"""Problem endpoints.

Provides read-only APIs for listing, fetching, and searching problems.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_problem_service
from app.schemas.problem import ProblemListResponse, ProblemResponse

router = APIRouter(prefix="/problems", tags=["Problems"])


@router.get("", response_model=ProblemListResponse)
async def list_problems(problem_service=Depends(get_problem_service)) -> ProblemListResponse:
    """List all problems."""

    problems = problem_service.get_all_problems()
    return ProblemListResponse(items=problems, total=len(problems))


@router.get("/search", response_model=ProblemListResponse)
async def search_problems(
    keyword: str,
    problem_service=Depends(get_problem_service),
) -> ProblemListResponse:
    """Search problems by keyword."""

    problems = problem_service.search_problems(keyword)
    return ProblemListResponse(items=problems, total=len(problems))


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(
    problem_id: UUID,
    problem_service=Depends(get_problem_service),
) -> ProblemResponse:
    """Fetch a problem by id."""

    problem = problem_service.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

