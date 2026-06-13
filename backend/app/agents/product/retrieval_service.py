import faiss
import numpy as np

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class RetrievalService:

    def __init__(
        self,
        db: AsyncSession,
        index_path: str,
    ):
        self.db = db
        self.index = faiss.read_index(
            index_path
        )

    async def retrieve(
        self,
        embedding: list[float],
        top_k: int = 20,
    ):

        query = np.array(
            [embedding],
            dtype="float32",
        )

        distances, ids = self.index.search(
            query,
            top_k,
        )

        product_ids = ids[0].tolist()

        stmt = select(Product).where(
            Product.id.in_(product_ids)
        )

        result = await self.db.execute(stmt)

        products = result.scalars().all()

        score_map = {
            product_ids[i]: float(
                distances[0][i]
            )
            for i in range(len(product_ids))
        }

        return products, score_map