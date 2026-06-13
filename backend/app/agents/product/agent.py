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


class ProductAgent:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
    ):
        self.embedding_service = (
            embedding_service
        )

        self.retrieval_service = (
            retrieval_service
        )

    async def recommend(
        self,
        situation: str,
        urgency: str,
        budget: float | None,
        memory,
        category: str,
    ) -> ProductResponse:

        embedding = (
            await self.embedding_service
            .generate_embedding(
                situation
            )
        )

        products, score_map = (
            await self.retrieval_service
            .retrieve(
                embedding
            )
        )

        ranked = RankingService.rank(
            products=products,
            score_map=score_map,
            memory=memory,
            urgency=urgency,
            budget=budget,
        )

        top_products = []

        for product, score, similarity in ranked[:10]:

            top_products.append(
                ProductCandidate(
                    product_id=product.id,
                    title=product.title,
                    category=product.category,
                    price=product.price,
                    similarity_score=similarity,
                    ranking_score=score,
                )
            )

        bundle_products = (
            BundleService.generate(
                category,
                products,
            )
        )

        bundle_candidates = []

        for product in bundle_products:

            bundle_candidates.append(
                ProductCandidate(
                    product_id=product.id,
                    title=product.title,
                    category=product.category,
                    price=product.price,
                    similarity_score=0,
                    ranking_score=0,
                )
            )

        confidence = round(
            (
                sum(
                    p.similarity_score
                    for p in top_products[:3]
                )
                / 3
            ),
            2,
        )

        return ProductResponse(
            top_products=top_products,
            bundle_products=bundle_candidates,
            confidence=confidence,
        )