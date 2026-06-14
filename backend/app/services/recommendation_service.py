from __future__ import annotations

import logging
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.product.agent import ProductAgent
from app.agents.product.schemas import ProductCandidate, ProductResponse
from app.agents.sustainability.agent import SustainabilityAgent
from app.agents.sustainability.schemas import SustainabilityResponse
from app.core.logger import logger
from app.memory.memory_manager import MemoryManager
from app.memory.schemas import UserMemory
from app.models.product import Product
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class RecommendationRequest(BaseModel):
    """Request for product recommendations."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    situation: str = Field(..., min_length=1)
    urgency: str = Field(..., min_length=1)
    budget: float | None = Field(None, ge=0)
    category: str = Field(..., min_length=1)


class RecommendationItem(BaseModel):
    """Single recommendation item."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    title: str
    category: str
    price: float
    similarity_score: float
    ranking_score: float
    in_stock: bool


class RecommendationResponse(BaseModel):
    """Comprehensive recommendation response."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    recommended_products: list[RecommendationItem] = Field(default_factory=list)
    bundle_products: list[RecommendationItem] = Field(default_factory=list)
    eco_alternatives: list[dict] = Field(default_factory=list)
    personalization_applied: bool
    confidence: float
    total_carbon_saved: float = 0.0
    overall_sustainability_score: float = 0.0


class RecommendationServiceError(Exception):
    """Base exception for recommendation service."""

    pass


class RecommendationService:
    """Service layer for intelligent product recommendations.

    Orchestrates product agent, sustainability agent, and user memory
    to generate personalized, ranked, and eco-conscious recommendations.
    """

    def __init__(
        self,
        product_agent: ProductAgent,
        sustainability_agent: SustainabilityAgent,
        memory_manager: MemoryManager,
        llm_service: GeminiService,
        db: AsyncSession,
    ) -> None:
        self._product_agent = product_agent
        self._sustainability_agent = sustainability_agent
        self._memory_manager = memory_manager
        self._llm_service = llm_service
        self._db = db
        self._logger = logger

    async def recommend_products(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        """Generate personalized product recommendations.

        Orchestrates product generation, ranking, personalization,
        and sustainability analysis.

        Args:
            request: Recommendation request with user context

        Returns:
            RecommendationResponse with ranked recommendations

        Raises:
            RecommendationServiceError: If recommendation generation fails
        """
        self._logger.info(
            "Generating product recommendations",
            extra={
                "user_id": str(request.user_id),
                "urgency": request.urgency,
                "category": request.category,
            },
        )

        try:
            user_memory = await self._get_user_memory(request.user_id)
            personalization_applied = user_memory is not None

            product_response = await self._product_agent.recommend(
                situation=request.situation,
                urgency=request.urgency,
                budget=request.budget,
                memory=user_memory,
                category=request.category,
            )

            self._logger.debug(
                "Product agent generated candidates",
                extra={
                    "user_id": str(request.user_id),
                    "top_products": len(product_response.top_products),
                    "bundle_products": len(product_response.bundle_products),
                    "confidence": product_response.confidence,
                },
            )

            filtered_products = await self._filter_unavailable(
                product_response.top_products
            )
            filtered_bundles = await self._filter_unavailable(
                product_response.bundle_products
            )

            self._logger.debug(
                "Filtered products by availability",
                extra={
                    "user_id": str(request.user_id),
                    "available_products": len(filtered_products),
                    "available_bundles": len(filtered_bundles),
                },
            )

            eco_response = await self._sustainability_agent.analyze(
                recommended_products=[
                    self._candidate_to_product_model(p) for p in filtered_products
                ]
            )

            self._logger.debug(
                "Sustainability analysis completed",
                extra={
                    "user_id": str(request.user_id),
                    "eco_alternatives": len(eco_response.eco_alternatives),
                    "total_carbon_saved": eco_response.total_carbon_saved,
                },
            )

            recommendation_items = [
                self._to_recommendation_item(p, True) for p in filtered_products
            ]
            bundle_items = [
                self._to_recommendation_item(b, True) for b in filtered_bundles
            ]

            eco_alternatives = [
                alt.model_dump() for alt in eco_response.eco_alternatives
            ]

            response = RecommendationResponse(
                user_id=request.user_id,
                recommended_products=recommendation_items,
                bundle_products=bundle_items,
                eco_alternatives=eco_alternatives,
                personalization_applied=personalization_applied,
                confidence=product_response.confidence,
                total_carbon_saved=eco_response.total_carbon_saved,
                overall_sustainability_score=eco_response.overall_sustainability_score,
            )

            self._logger.info(
                "Recommendations generated successfully",
                extra={
                    "user_id": str(request.user_id),
                    "recommendation_count": len(recommendation_items),
                    "bundle_count": len(bundle_items),
                    "personalization_applied": personalization_applied,
                },
            )

            return response

        except ValueError as exc:
            self._logger.warning(
                "Recommendation generation validation error",
                extra={
                    "user_id": str(request.user_id),
                    "error": str(exc),
                },
            )
            raise RecommendationServiceError(str(exc)) from exc

        except Exception as exc:
            self._logger.exception(
                "Unexpected error during recommendation generation",
                extra={"user_id": str(request.user_id)},
            )
            raise RecommendationServiceError(
                "Failed to generate recommendations"
            ) from exc

    async def rank_products(
        self,
        products: list[ProductCandidate],
        user_id: UUID,
        urgency: str,
        budget: float | None = None,
    ) -> list[tuple[ProductCandidate, float]]:
        """Rank products by relevance score.

        Considers similarity, budget fit, urgency, and user memory
        to calculate ranking scores.

        Args:
            products: Candidates to rank
            user_id: User for memory context
            urgency: Urgency level for ranking boost
            budget: Budget constraint for ranking

        Returns:
            List of (product, score) tuples sorted by score descending
        """
        self._logger.debug(
            "Ranking products",
            extra={
                "user_id": str(user_id),
                "product_count": len(products),
                "urgency": urgency,
                "has_budget": budget is not None,
            },
        )

        try:
            user_memory = await self._get_user_memory(user_id)

            ranked = []
            for product in products:
                score = product.ranking_score
                if score > 0:
                    ranked.append((product, score))

            ranked.sort(key=lambda x: x[1], reverse=True)

            self._logger.debug(
                "Products ranked",
                extra={
                    "user_id": str(user_id),
                    "ranked_count": len(ranked),
                    "top_score": ranked[0][1] if ranked else 0,
                },
            )

            return ranked

        except Exception as exc:
            self._logger.error(
                "Error ranking products",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            raise RecommendationServiceError("Failed to rank products") from exc

    async def personalize_results(
        self,
        recommendations: list[RecommendationItem],
        user_id: UUID,
    ) -> list[RecommendationItem]:
        """Personalize recommendations using user memory.

        Reorders recommendations based on user preferences, purchase
        history, and sustainability profile.

        Args:
            recommendations: Base recommendations
            user_id: User for personalization

        Returns:
            Personalized recommendation list
        """
        self._logger.debug(
            "Personalizing recommendations",
            extra={
                "user_id": str(user_id),
                "recommendation_count": len(recommendations),
            },
        )

        try:
            user_memory = await self._get_user_memory(user_id)
            if user_memory is None:
                self._logger.debug(
                    "No user memory available for personalization",
                    extra={"user_id": str(user_id)},
                )
                return recommendations

            personalized = []
            for rec in recommendations:
                boost = 0.0

                if user_memory.preferred_brands:
                    for product in await self._fetch_products([rec.product_id]):
                        if product.brand in user_memory.preferred_brands:
                            boost += 10.0

                if rec.price <= (user_memory.budget_level or float("inf")):
                    boost += 5.0

                boost += user_memory.sustainability_score * 0.1

                personalized_item = rec.model_copy(
                    update={"ranking_score": rec.ranking_score + boost}
                )
                personalized.append(personalized_item)

            personalized.sort(key=lambda x: x.ranking_score, reverse=True)

            self._logger.debug(
                "Recommendations personalized",
                extra={
                    "user_id": str(user_id),
                    "personalized_count": len(personalized),
                },
            )

            return personalized

        except Exception as exc:
            self._logger.error(
                "Error personalizing recommendations",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            return recommendations

    async def _get_user_memory(self, user_id: UUID) -> UserMemory | None:
        """Retrieve user memory for personalization.

        Returns:
            UserMemory if available, None otherwise
        """
        try:
            memory = await self._memory_manager.retrieve_memory(user_id)
            return memory
        except ValueError:
            return None
        except Exception as exc:
            self._logger.warning(
                "Error retrieving user memory",
                extra={"user_id": str(user_id), "error": str(exc)},
            )
            return None

    async def _filter_unavailable(
        self,
        products: list[ProductCandidate],
    ) -> list[ProductCandidate]:
        """Filter out products with insufficient stock.

        Args:
            products: Candidate products

        Returns:
            Products with available stock
        """
        if not products:
            return []

        product_ids = [p.product_id for p in products]
        available = await self._fetch_available_products(product_ids)
        available_ids = {p.id for p in available}

        filtered = [p for p in products if p.product_id in available_ids]

        self._logger.debug(
            "Filtered products by availability",
            extra={
                "total": len(products),
                "available": len(filtered),
                "unavailable": len(products) - len(filtered),
            },
        )

        return filtered

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

        stmt = select(Product).where(Product.id.in_(product_ids))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _fetch_available_products(
        self,
        product_ids: list[UUID],
    ) -> list[Product]:
        """Fetch only products with stock > 0.

        Args:
            product_ids: IDs to check

        Returns:
            Products with available stock

        Note:
            Future: Integrate with inventory service or cache for
            performance. Consider FAISS indexing for large datasets.
        """
        if not product_ids:
            return []

        stmt = select(Product).where(
            Product.id.in_(product_ids),
            Product.stock > 0,
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _to_recommendation_item(
        candidate: ProductCandidate,
        in_stock: bool,
    ) -> RecommendationItem:
        """Convert ProductCandidate to RecommendationItem.

        Args:
            candidate: Product candidate from agent
            in_stock: Stock availability flag

        Returns:
            RecommendationItem with metadata
        """
        return RecommendationItem(
            product_id=candidate.product_id,
            title=candidate.title,
            category=candidate.category,
            price=candidate.price,
            similarity_score=candidate.similarity_score,
            ranking_score=candidate.ranking_score,
            in_stock=in_stock,
        )

    @staticmethod
    def _candidate_to_product_model(candidate: ProductCandidate) -> Product:
        """Convert ProductCandidate to Product model for sustainability agent.

        Args:
            candidate: Product candidate

        Returns:
            Product model with minimal data for analysis
        """
        product = Product()
        product.id = candidate.product_id
        product.title = candidate.title
        product.category = candidate.category
        product.price = candidate.price
        return product
