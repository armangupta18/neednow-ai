from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import logger
from app.dependencies.memory import get_memory_manager
from app.memory.memory_manager import MemoryManager
from app.memory.schemas import UserMemory
from app.schemas.memory import ClearMemoryResponse, MemoryResponse, StoreMemoryRequest

router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.post(
    "/store",
    response_model=MemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Store user memory",
)
async def store_memory(
    request: StoreMemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> MemoryResponse:
    try:
        stored = await memory_manager.save_memory(
            user_id=request.user_id,
            memory=request.memory,
        )

        logger.info(
            "Stored user memory",
            extra={"user_id": str(request.user_id)},
        )

        return MemoryResponse(
            user_id=request.user_id,
            memory=UserMemory(**stored),
        )

    except ValueError as exc:
        logger.warning(
            "Memory store validation error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Failed to store user memory",
            extra={"user_id": str(request.user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store user memory",
        )


@router.get(
    "/{user_id}",
    response_model=MemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve user memory",
)
async def get_memory(
    user_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> MemoryResponse:
    try:
        memory = await memory_manager.retrieve_memory(user_id)

        logger.info(
            "Retrieved user memory",
            extra={"user_id": str(user_id)},
        )

        return MemoryResponse(
            user_id=user_id,
            memory=memory,
        )

    except ValueError as exc:
        logger.warning(
            "Memory retrieval validation error",
            extra={"user_id": str(user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Failed to retrieve user memory",
            extra={"user_id": str(user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user memory",
        )


@router.delete(
    "/{user_id}",
    response_model=ClearMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear user memory",
)
async def clear_memory(
    user_id: UUID,
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> ClearMemoryResponse:
    try:
        await memory_manager.save_memory(
            user_id=user_id,
            memory=UserMemory(),
        )

        logger.info(
            "Cleared user memory",
            extra={"user_id": str(user_id)},
        )

        return ClearMemoryResponse(user_id=user_id)

    except ValueError as exc:
        logger.warning(
            "Memory clear validation error",
            extra={"user_id": str(user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Failed to clear user memory",
            extra={"user_id": str(user_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear user memory",
        )
