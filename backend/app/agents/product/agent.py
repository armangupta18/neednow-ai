"""Product recommendation agent powered by Gemini.

Uses vector/DB retrieval to find candidate products, then
applies Gemini structured prompting to select and rank
the top 4 most relevant recommendations with reasoning.
"""

import json
import logging

from pydantic import BaseModel, Field, field_validator

from app.agents.product.schemas import (
    ProductCandidate,
    ProductResponse,
)
from app.agents.product.embedding_service import (
    EmbeddingService,
)
from app.agents.product.retrieval_service import (
    RetrievalService,
)
from app.agents.product.ranking_service import (
    RankingService,
)
from app.agents.product.bundle_service import (
    BundleService,
)
from app.agents.product.recommendation_prompt import (
    RECOMMENDATION_SYSTEM_PROMPT,
    build_recommendation_user_prompt,
)
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation schema for Gemini recommendation output
# ---------------------------------------------------------------------------


class RecommendationItem(BaseModel):
    """Validated recommendation from Gemini."""

    product_name: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=5)
    priority: int = Field(..., ge=1, le=4)

    @field_validator("priority")
    @classmethod
    def priority_in_range(cls, v: int) -> int:
        if v < 1 or v > 4:
            raise ValueError("Priority must be between 1 and 4")
        return v


class RecommendationOutput(BaseModel):
    """Validated Gemini response."""

    recommendations: list[RecommendationItem] = Field(..., max_length=4)

    @field_validator("recommendations")
    @classmethod
    def max_four_items(cls, v: list[RecommendationItem]) -> list[RecommendationItem]:
        if len(v) > 4:
            return v[:4]
        return v


# ---------------------------------------------------------------------------
# Product Agent
# ---------------------------------------------------------------------------


class ProductAgent:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
        llm_service: GeminiService | None = None,
    ):
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.llm = llm_service or GeminiService()

    async def recommend(
        self,
        situation: str,
        urgency: str,
        budget: float | None,
        memory,
        category: str,
    ) -> ProductResponse:
        """Generate product recommendations using Gemini + retrieval.

        Flow:
        1. Generate embedding for the situation text.
        2. Retrieve candidate products from DB/FAISS.
        3. Rank candidates using scoring heuristics.
        4. Send top candidates to Gemini for structured recommendation.
        5. Match Gemini selections back to product records.
        6. Return max 4 validated products.
        """

        # Step 1: Embedding
        embedding = await self.embedding_service.generate_embedding(situation)

        # Step 2: Retrieval
        products, score_map = await self.retrieval_service.retrieve(
            embedding,
            category=category,
            situation=situation,
        )

        # Step 3: Rank candidates
        ranked = RankingService.rank(
            products=products,
            score_map=score_map,
            memory=memory,
            urgency=urgency,
            budget=budget,
        )

        # Step 4: Use Gemini to generate structured recommendations
        # Take top 10 candidates for Gemini to choose from
        candidates_for_gemini = ranked[:10]
        available_products = [
            {"title": product.title, "price": product.price, "id": str(product.id)}
            for product, score, similarity in candidates_for_gemini
        ]

        gemini_recommendations = await self._generate_recommendations(
            situation=situation,
            category=category,
            urgency=urgency,
            available_products=available_products,
        )

        # Step 5: Match Gemini selections back to product records
        top_products = self._match_recommendations(
            gemini_recommendations, ranked
        )

        # Fallback: if Gemini matching fails, use ranked order
        if not top_products:
            for product, score, similarity in ranked[:4]:
                top_products.append(
                    ProductCandidate(
                        product_id=product.id,
                        title=product.title,
                        category=product.category,
                        price=product.price,
                        similarity_score=similarity,
                        ranking_score=score,
                        reason="Matched by relevance scoring",
                        priority=len(top_products) + 1,
                    )
                )

        # Step 6: Bundle suggestions
        bundle_products = BundleService.generate(category, products)
        bundle_candidates = [
            ProductCandidate(
                product_id=product.id,
                title=product.title,
                category=product.category,
                price=product.price,
                similarity_score=0,
                ranking_score=0,
            )
            for product in bundle_products
        ]

        # Confidence score
        confidence = 0.0
        if top_products:
            top_scores = [p.similarity_score for p in top_products[:3]]
            confidence = round(sum(top_scores) / len(top_scores), 2) if top_scores else 0.0

        return ProductResponse(
            top_products=top_products[:4],
            bundle_products=bundle_candidates,
            confidence=confidence,
        )

    async def _generate_recommendations(
        self,
        situation: str,
        category: str,
        urgency: str,
        available_products: list[dict],
    ) -> list[RecommendationItem]:
        """Call Gemini to generate structured recommendations."""
        if not available_products:
            return []

        try:
            user_prompt = build_recommendation_user_prompt(
                situation=situation,
                category=category,
                urgency=urgency,
                available_products=available_products,
            )

            raw_response = await self.llm.invoke(
                system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            # Parse and validate
            parsed = self._parse_gemini_response(raw_response)
            logger.info(
                "Gemini recommended %d products for situation: %s",
                len(parsed),
                situation[:50],
            )
            return parsed

        except Exception as exc:
            logger.warning(
                "Gemini recommendation generation failed: %s. Using ranking fallback.",
                exc,
            )
            return []

    @staticmethod
    def _parse_gemini_response(raw: str) -> list[RecommendationItem]:
        """Parse and validate Gemini JSON response."""
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "").strip()

        data = json.loads(cleaned)

        # Validate with Pydantic
        output = RecommendationOutput(**data)
        return output.recommendations

    def _match_recommendations(
        self,
        recommendations: list[RecommendationItem],
        ranked_products: list,
    ) -> list[ProductCandidate]:
        """Match Gemini recommendation names to actual product records."""
        if not recommendations:
            return []

        # Build lookup by normalized title
        product_lookup: dict[str, tuple] = {}
        for product, score, similarity in ranked_products:
            key = product.title.lower().strip()
            product_lookup[key] = (product, score, similarity)

        matched: list[ProductCandidate] = []
        for rec in sorted(recommendations, key=lambda r: r.priority):
            # Try exact match first
            key = rec.product_name.lower().strip()
            match = product_lookup.get(key)

            # Try fuzzy partial match if exact fails
            if not match:
                for title_key, data in product_lookup.items():
                    if key in title_key or title_key in key:
                        match = data
                        break

            if match:
                product, score, similarity = match
                matched.append(
                    ProductCandidate(
                        product_id=product.id,
                        title=product.title,
                        category=product.category,
                        price=product.price,
                        similarity_score=similarity,
                        ranking_score=score,
                        reason=rec.reason,
                        priority=rec.priority,
                    )
                )

        return matched[:4]
