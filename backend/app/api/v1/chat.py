from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.shared.base_agent import AgentExecutionError, AgentValidationError
from app.core.logger import logger
from app.dependencies.chat import get_chat_service
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description=(
        "Process a user message through the supervisor agent pipeline and "
        "return an assistant reply with cart, urgency, and sustainability data."
    ),
)
async def send_chat_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        return await chat_service.process_message(request)

    except ValueError as exc:
        logger.warning(
            "Chat validation error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        logger.warning(
            "Chat authorization error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except (AgentValidationError, AgentExecutionError) as exc:
        logger.warning(
            "Chat agent error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Chat pipeline failed",
            extra={"user_id": str(request.user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message",
        )


@router.get(
    "/{session_id}/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session history",
)
async def get_chat_history(
    session_id: UUID,
    user_id: UUID,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatHistoryResponse:
    try:
        return chat_service.get_history(
            session_id=session_id,
            user_id=user_id,
        )

    except PermissionError as exc:
        logger.warning(
            "Chat history authorization error",
            extra={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Failed to retrieve chat history",
            extra={
                "session_id": str(session_id),
                "user_id": str(user_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history",
        )
