from __future__ import annotations

import logging
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.sustainability.agent import SustainabilityAgent
from app.agents.sustainability.carbon_service import CarbonService
from app.agents.sustainability.schemas import SustainabilityResponse
from app.agents.sustainability.scoring_service import SustainabilityScoringService
from app.core.logger import logger
from app.models.product import Product
from app.schemas.sustainability import (
    ProductEcoScoreResponse,
    SustainabilityRecommendResponse,
    SustainabilityReportResponse,
)

logger = logging.getLogger(__name__)


class EcoScoreMetrics(BaseModel):
    """Detailed eco score breakdown."""

    model_config = ConfigDict(extra="forbid")

    base_score: float = Field(..., ge=0, le=100)
    category_bonus: float = Field(default=0.0)
    material_bonus: float = Field(default=0.0)
    sustainability_rating: str = Field(...)
    carbon_footprint_kg: float = Field(...)


class ResaleRecommendation(BaseModel):
    """Resale value recommendation for a product."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    product_name: str
    current_price: float
    estimated_resale_value: float
    resale_percentage: float = Field(ge=0, le=100)
    recommended_platforms: list[str] = Field(default_factory=list)
    environmental_impact: str


class SustainabilityServiceError(Exception):
    """Base exception for sustainability service errors."""

    pass


class ProductNotFoundError(SustainabilityServiceError):
    """Raised when product is not found."""

    pass


class EcoAnalysisError(SustainabilityServiceError):
    """Raised when eco analysis fails."""

    pass


class SustainabilityService:
    """Service layer for sustainability analysis, eco-scoring, and recommendations.

    Orchestrates sustainability agent, eco score calculations, carbon footprint
    estimation, and eco-alternative discovery.
    """

    def __init__(
        self,
        sustainability_agent: SustainabilityAgent,
        db: AsyncSession,
    ) -> None:
        self._agent = sustainability_agent
        self._db = db
        self._logger = logger

    async def calculate_score(
        self,
        product_id: UUID,
    ) -> ProductEcoScoreResponse:
        """Calculate detailed eco score for a single product.

        Args:
            product_id: Product identifier

        Returns:
            ProductEcoScoreResponse with eco score

        Raises:
            ProductNotFoundError: If product not found
        """
        self._logger.info(
            "Calculating eco score",
            extra={"product_id": str(product_id)},
        )

        try:
            product = await self._fetch_product(product_id)
            if product is None:
                self._logger.warning(
                    "Product not found for eco score calculation",
                    extra={"product_id": str(product_id)},
                )
                raise ProductNotFoundError(f"Product {product_id} not found")

            score = SustainabilityScoringService.calculate_score(product)
            carbon_footprint = CarbonService.estimate(product.category)

            self._logger.debug(
                "Eco score calculated",
                extra={
                    "product_id": str(product_id),
                    "score": score,
                    "carbon": carbon_footprint,
                },
            )

            return ProductEcoScoreResponse(
                product_id=product.id,
                product_name=product.title,
                category=product.category,
                sustainability_score=score,
            )

        except ProductNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Error calculating eco score",
                extra={"product_id": str(product_id), "error": str(exc)},
            )
            raise EcoAnalysisError(f"Failed to calculate eco score: {str(exc)}") from exc

    async def recommend_alternatives(
        self,
        product_ids: list[UUID],
    ) -> SustainabilityRecommendResponse:
        """Recommend eco-friendly alternatives for given products.

        Args:
            product_ids: Product identifiers to find alternatives for

        Returns:
            SustainabilityRecommendResponse with alternatives

        Raises:
            ProductNotFoundError: If no products found
            EcoAnalysisError: If analysis fails
        """
        self._logger.info(
            "Recommending eco alternatives",
            extra={
                "product_count": len(product_ids),
                "product_ids": [str(pid) for pid in product_ids],
            },
        )

        try:
            products = await self._fetch_products(product_ids)
            if not products:
                self._logger.warning(
                    "No products found for alternative recommendations",
                    extra={"product_ids": [str(pid) for pid in product_ids]},
                )
                raise ProductNotFoundError(
                    "No products found for the provided identifiers"
                )

            self._logger.debug(
                "Fetched products for analysis",
                extra={
                    "requested": len(product_ids),
                    "found": len(products),
                },
            )

            result = await self._agent.analyze(products)

            self._logger.info(
                "Eco alternatives recommended",
                extra={
                    "product_count": len(products),
                    "alternatives_found": len(result.eco_alternatives),
                    "total_carbon_saved": result.total_carbon_saved,
                    "overall_score": result.overall_sustainability_score,
                },
            )

            return SustainabilityRecommendResponse(
                recommendations=result.eco_alternatives,
                total_carbon_saved=result.total_carbon_saved,
                overall_sustainability_score=result.overall_sustainability_score,
            )

        except ProductNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Error recommending alternatives",
                extra={
                    "product_count": len(product_ids),
                    "error": str(exc),
                },
            )
            raise EcoAnalysisError(
                f"Failed to recommend alternatives: {str(exc)}"
            ) from exc

    async def generate_report(
        self,
        product_ids: list[UUID],
    ) -> SustainabilityReportResponse:
        """Generate comprehensive sustainability report for products.

        Args:
            product_ids: Product identifiers for report

        Returns:
            SustainabilityReportResponse with full analysis

        Raises:
            ProductNotFoundError: If no products found
            EcoAnalysisError: If analysis fails
        """
        self._logger.info(
            "Generating sustainability report",
            extra={
                "product_count": len(product_ids),
                "product_ids": [str(pid) for pid in product_ids][:5],
            },
        )

        try:
            products = await self._fetch_products(product_ids)
            if not products:
                self._logger.warning(
                    "No products found for report generation",
                    extra={"product_ids": [str(pid) for pid in product_ids]},
                )
                raise ProductNotFoundError(
                    "No products found for the provided identifiers"
                )

            self._logger.debug(
                "Running sustainability agent analysis",
                extra={"product_count": len(products)},
            )

            result = await self._agent.analyze(products)

            report = self._to_report_response(result)

            self._logger.info(
                "Sustainability report generated",
                extra={
                    "product_count": len(products),
                    "alternatives": len(report.eco_alternatives),
                    "carbon_saved": report.total_carbon_saved,
                    "overall_score": report.overall_sustainability_score,
                },
            )

            return report

        except ProductNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Error generating sustainability report",
                extra={
                    "product_count": len(product_ids),
                    "error": str(exc),
                },
            )
            raise EcoAnalysisError(
                f"Failed to generate sustainability report: {str(exc)}"
            ) from exc

    async def get_resale_recommendation(
        self,
        product_id: UUID,
    ) -> ResaleRecommendation:
        """Get resale value recommendation for a product.

        Estimates resale value based on category, sustainability score,
        and market conditions. Higher eco-score products typically retain
        better resale value.

        Args:
            product_id: Product identifier

        Returns:
            ResaleRecommendation with value estimates

        Raises:
            ProductNotFoundError: If product not found
        """
        self._logger.info(
            "Getting resale recommendation",
            extra={"product_id": str(product_id)},
        )

        try:
            product = await self._fetch_product(product_id)
            if product is None:
                self._logger.warning(
                    "Product not found for resale recommendation",
                    extra={"product_id": str(product_id)},
                )
                raise ProductNotFoundError(f"Product {product_id} not found")

            eco_score = SustainabilityScoringService.calculate_score(product)

            resale_percentage = self._calculate_resale_percentage(eco_score)
            estimated_resale_value = product.price * (resale_percentage / 100)

            rating = self._get_sustainability_rating(eco_score)
            platforms = self._recommend_resale_platforms(product.category)

            self._logger.debug(
                "Resale recommendation calculated",
                extra={
                    "product_id": str(product_id),
                    "resale_percentage": resale_percentage,
                    "estimated_value": estimated_resale_value,
                },
            )

            return ResaleRecommendation(
                product_id=product.id,
                product_name=product.title,
                current_price=product.price,
                estimated_resale_value=round(estimated_resale_value, 2),
                resale_percentage=round(resale_percentage, 1),
                recommended_platforms=platforms,
                environmental_impact=rating,
            )

        except ProductNotFoundError:
            raise
        except Exception as exc:
            self._logger.error(
                "Error calculating resale recommendation",
                extra={"product_id": str(product_id), "error": str(exc)},
            )
            raise EcoAnalysisError(
                f"Failed to calculate resale recommendation: {str(exc)}"
            ) from exc

    async def batch_calculate_scores(
        self,
        product_ids: list[UUID],
    ) -> dict[UUID, ProductEcoScoreResponse]:
        """Calculate eco scores for multiple products in batch.

        Args:
            product_ids: List of product identifiers

        Returns:
            Dictionary mapping product ID to eco score response

        Raises:
            EcoAnalysisError: If batch calculation fails
        """
        self._logger.info(
            "Batch calculating eco scores",
            extra={"product_count": len(product_ids)},
        )

        try:
            products = await self._fetch_products(product_ids)

            scores = {}
            for product in products:
                score = SustainabilityScoringService.calculate_score(product)
                scores[product.id] = ProductEcoScoreResponse(
                    product_id=product.id,
                    product_name=product.title,
                    category=product.category,
                    sustainability_score=score,
                )

            self._logger.debug(
                "Batch eco scores calculated",
                extra={"calculated": len(scores), "total": len(product_ids)},
            )

            return scores

        except Exception as exc:
            self._logger.error(
                "Error batch calculating scores",
                extra={"product_count": len(product_ids), "error": str(exc)},
            )
            raise EcoAnalysisError(
                f"Failed to batch calculate scores: {str(exc)}"
            ) from exc

    async def get_product_score(
        self,
        product_id: UUID,
    ) -> ProductEcoScoreResponse:
        """Legacy method for compatibility. Use calculate_score() instead.

        Args:
            product_id: Product identifier

        Returns:
            ProductEcoScoreResponse with eco score
        """
        return await self.calculate_score(product_id)

    async def _fetch_products(
        self,
        product_ids: list[UUID],
    ) -> list[Product]:
        """Fetch products from database.

        Args:
            product_ids: IDs to fetch

        Returns:
            List of Product models
        """
        if not product_ids:
            return []

        try:
            stmt = select(Product).where(Product.id.in_(product_ids))
            result = await self._db.execute(stmt)
            products = list(result.scalars().all())

            self._logger.debug(
                "Products fetched",
                extra={"requested": len(product_ids), "found": len(products)},
            )

            return products

        except Exception as exc:
            self._logger.error(
                "Error fetching products",
                extra={"count": len(product_ids), "error": str(exc)},
            )
            raise

    async def _fetch_product(
        self,
        product_id: UUID,
    ) -> Product | None:
        """Fetch single product from database.

        Args:
            product_id: Product identifier

        Returns:
            Product model or None if not found
        """
        try:
            stmt = select(Product).where(Product.id == product_id)
            result = await self._db.execute(stmt)
            product = result.scalar_one_or_none()

            self._logger.debug(
                "Product fetched",
                extra={"product_id": str(product_id), "found": product is not None},
            )

            return product

        except Exception as exc:
            self._logger.error(
                "Error fetching product",
                extra={"product_id": str(product_id), "error": str(exc)},
            )
            raise

    @staticmethod
    def _to_report_response(
        result: SustainabilityResponse,
    ) -> SustainabilityReportResponse:
        """Convert SustainabilityResponse to SustainabilityReportResponse.

        Args:
            result: Raw sustainability analysis result

        Returns:
            Formatted report response
        """
        return SustainabilityReportResponse(
            eco_alternatives=result.eco_alternatives,
            total_carbon_saved=result.total_carbon_saved,
            overall_sustainability_score=result.overall_sustainability_score,
        )

    @staticmethod
    def _calculate_resale_percentage(eco_score: float) -> float:
        """Calculate estimated resale percentage based on eco score.

        Higher eco-score products retain better value due to:
        - Growing sustainability awareness
        - Better market demand
        - Lower environmental impact premium

        Args:
            eco_score: Sustainability eco score (0-100)

        Returns:
            Estimated resale percentage (0-100)
        """
        if eco_score >= 80:
            return 75.0
        elif eco_score >= 60:
            return 60.0
        elif eco_score >= 40:
            return 50.0
        else:
            return 35.0

    @staticmethod
    def _get_sustainability_rating(eco_score: float) -> str:
        """Get sustainability rating label.

        Args:
            eco_score: Eco score (0-100)

        Returns:
            Rating string (Excellent/Good/Fair/Poor)
        """
        if eco_score >= 80:
            return "Excellent"
        elif eco_score >= 60:
            return "Good"
        elif eco_score >= 40:
            return "Fair"
        else:
            return "Poor"

    @staticmethod
    def _recommend_resale_platforms(category: str) -> list[str]:
        """Recommend resale platforms based on product category.

        Args:
            category: Product category

        Returns:
            List of recommended resale platforms
        """
        category_lower = category.lower()

        platform_map = {
            "electronics": ["eBay", "Facebook Marketplace", "Swappa"],
            "clothing": ["Depop", "Vinted", "Mercari", "Poshmark"],
            "household": ["Facebook Marketplace", "OfferUp", "Craigslist"],
            "furniture": ["Facebook Marketplace", "OfferUp", "Letgo"],
            "books": ["AbeBooks", "Vinted", "eBay"],
            "organic": ["Local Community Groups", "Farmers Markets"],
            "food": ["Local Food Banks", "Community Share Programs"],
        }

        for key, platforms in platform_map.items():
            if key in category_lower:
                return platforms

        return ["Facebook Marketplace", "OfferUp", "eBay"]

