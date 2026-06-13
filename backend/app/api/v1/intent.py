from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.schemas.intent import (
    IntentRequest,
)

from app.agents.supervisor.agent import (
    SupervisorAgent,
)

from app.dependencies.supervisor import (
    get_supervisor,
)

from app.core.logger import logger


router = APIRouter(
    prefix="/intent",
    tags=["Intent"],
)


@router.post("")
async def create_cart_from_intent(
    request: IntentRequest,
    supervisor: SupervisorAgent = Depends(
        get_supervisor
    ),
):

    try:

        response = (
            await supervisor.execute(
                user_id=request.user_id,
                situation=request.text,
            )
        )

        return response.model_dump()

    except ValueError as e:

        logger.warning(
            f"Validation error: {e}"
        )

        raise HTTPException(
            status_code=
            status.HTTP_400_BAD_REQUEST,

            detail=str(e),
        )

    except Exception as e:

        logger.exception(
            "Intent pipeline failed"
        )

        raise HTTPException(
            status_code=
            status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
            "Failed to process request",
        )