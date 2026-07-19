"""AtlasAI RAG ask endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai import (
    AIServiceError,
    ChatGenerationError,
    EmptyVectorStoreError,
    MissingConfigurationError,
    RetrievalError,
)

from app.api.v1.dependencies import get_ai_chat_service
from app.schemas.ask import AskAIRequest, AskAIResponse


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ai.chat import AtlasAIRAGChatService

router = APIRouter(prefix="/ask", tags=["AI"])

@router.post("", response_model=AskAIResponse, status_code=status.HTTP_200_OK)
async def ask_ai(
    payload: AskAIRequest,
    chat_service: AtlasAIRAGChatService = Depends(get_ai_chat_service),
) -> AskAIResponse:
    """Answer a natural-language question using AtlasAI's RAG pipeline."""

    try:
        result = chat_service.ask(question=payload.question)
    except MissingConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except EmptyVectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (RetrievalError, ChatGenerationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return AskAIResponse(
        answer=result.answer,
        sources=result.citations,
        metadata=result.metadata,
    )
