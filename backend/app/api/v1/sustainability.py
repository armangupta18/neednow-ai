from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.sustainability.exceptions import SustainabilityAgentException
from app.core.logger import logger
from app.dependencies.sustainability import get_sustainability_service
from app.schemas.sustainability import (
    ProductEcoScoreResponse,
    SustainabilityAnalyzeRequest,
    SustainabilityRecommendRequest,
    SustainabilityRecommendResponse,
    SustainabilityReportResponse,
)
from app.services.sustainability_service import SustainabilityService

router = APIRouter(
    prefix="/sustainability",
    tags=["Sustainability"],
)


@router.post(
    "/analyze",
    response_model=SustainabilityReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate sustainability report",
)
async def analyze_sustainability(
    request: SustainabilityAnalyzeRequest,
    sustainability_service: SustainabilityService = Depends(get_sustainability_service),
) -> SustainabilityReportResponse:
    try:
        response = await sustainability_service.generate_report(
            product_ids=request.product_ids,
        )

        logger.info(
            "Sustainability report generated",
            extra={
                "product_count": len(request.product_ids),
                "overall_score": response.overall_sustainability_score,
                "alternatives_found": len(response.eco_alternatives),
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Sustainability analyze validation error",
            extra={
                "product_ids": [str(pid) for pid in request.product_ids],
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except SustainabilityAgentException as exc:
        logger.warning(
            "Sustainability agent error",
            extra={
                "product_ids": [str(pid) for pid in request.product_ids],
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Sustainability analyze failed",
            extra={"product_ids": [str(pid) for pid in request.product_ids]},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sustainability report",
        )


@router.post(
    "/recommend",
    response_model=SustainabilityRecommendResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend eco-friendly alternatives",
)
async def recommend_sustainability(
    request: SustainabilityRecommendRequest,
    sustainability_service: SustainabilityService = Depends(get_sustainability_service),
) -> SustainabilityRecommendResponse:
    try:
        response = await sustainability_service.recommend_alternatives(
            product_ids=request.product_ids,
        )

        logger.info(
            "Sustainability recommendations generated",
            extra={
                "product_count": len(request.product_ids),
                "recommendation_count": len(response.recommendations),
                "overall_score": response.overall_sustainability_score,
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Sustainability recommend validation error",
            extra={
                "product_ids": [str(pid) for pid in request.product_ids],
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except SustainabilityAgentException as exc:
        logger.warning(
            "Sustainability recommendation agent error",
            extra={
                "product_ids": [str(pid) for pid in request.product_ids],
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Sustainability recommend failed",
            extra={"product_ids": [str(pid) for pid in request.product_ids]},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sustainability recommendations",
        )


@router.get(
    "/score/{product_id}",
    response_model=ProductEcoScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product eco score",
)
async def get_product_eco_score(
    product_id: UUID,
    sustainability_service: SustainabilityService = Depends(get_sustainability_service),
) -> ProductEcoScoreResponse:
    try:
        response = await sustainability_service.get_product_score(product_id)

        logger.info(
            "Product eco score retrieved",
            extra={
                "product_id": str(product_id),
                "sustainability_score": response.sustainability_score,
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Product eco score validation error",
            extra={"product_id": str(product_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Failed to retrieve product eco score",
            extra={"product_id": str(product_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product eco score",
        )
