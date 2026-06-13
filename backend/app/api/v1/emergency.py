from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.urgency.exceptions import UrgencyAgentException
from app.core.logger import logger
from app.dependencies.emergency import get_emergency_service
from app.schemas.emergency import (
    EmergencyAnalyzeRequest,
    EmergencyAnalyzeResponse,
    EmergencyEscalateRequest,
    EmergencyEscalateResponse,
    EmergencyHealthResponse,
)
from app.services.emergency_service import EmergencyService

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency"],
)


@router.post(
    "/analyze",
    response_model=EmergencyAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze urgency level",
)
async def analyze_emergency(
    request: EmergencyAnalyzeRequest,
    emergency_service: EmergencyService = Depends(get_emergency_service),
) -> EmergencyAnalyzeResponse:
    try:
        response = await emergency_service.analyze_urgency(
            user_id=request.user_id,
            text=request.text,
            user_context=request.user_context or None,
        )

        logger.info(
            "Emergency urgency analyzed",
            extra={
                "user_id": str(request.user_id),
                "urgency": response.urgency.value,
                "score": response.score,
                "is_emergency": response.is_emergency,
            },
        )

        return response

    except UrgencyAgentException as exc:
        logger.warning(
            "Emergency urgency agent error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        logger.warning(
            "Emergency analyze validation error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Emergency analyze failed",
            extra={"user_id": str(request.user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze emergency urgency",
        )


@router.post(
    "/escalate",
    response_model=EmergencyEscalateResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger emergency workflow",
)
async def escalate_emergency(
    request: EmergencyEscalateRequest,
    emergency_service: EmergencyService = Depends(get_emergency_service),
) -> EmergencyEscalateResponse:
    try:
        response = await emergency_service.escalate_emergency(
            user_id=request.user_id,
            text=request.text,
            user_context=request.user_context or None,
            contact_phone=request.contact_phone,
        )

        logger.info(
            "Emergency escalation processed",
            extra={
                "user_id": str(request.user_id),
                "escalated": response.escalated,
                "workflow_id": response.workflow_id,
                "urgency": response.urgency.value,
            },
        )

        return response

    except UrgencyAgentException as exc:
        logger.warning(
            "Emergency escalation agent error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        logger.warning(
            "Emergency escalate validation error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Emergency escalation failed",
            extra={"user_id": str(request.user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to escalate emergency workflow",
        )


@router.get(
    "/health",
    response_model=EmergencyHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Emergency subsystem health check",
)
async def emergency_health(
    emergency_service: EmergencyService = Depends(get_emergency_service),
) -> EmergencyHealthResponse:
    try:
        response = emergency_service.health_check()

        logger.debug(
            "Emergency health check succeeded",
            extra={"status": response.status},
        )

        return response

    except Exception:
        logger.exception("Emergency health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Emergency subsystem unavailable",
        )
