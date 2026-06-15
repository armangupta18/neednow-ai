"""Product retrieval service using FAISS vector search.

Retrieves semantically similar products from a FAISS index.
Operates in fallback mode (empty results) when the index file
is not available, allowing the application to start without FAISS.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger(__name__)

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]
    logger.info("faiss package not installed — using database retrieval.")


class RetrievalService:
    """Retrieves products via FAISS similarity search.

    If the FAISS index file does not exist at initialization,
    the service runs in fallback mode — returning empty results
    without raising exceptions. Once the index file is generated,
    the service will load it automatically on next instantiation.

    Args:
        db: SQLAlchemy AsyncSession for product lookups.
        index_path: Path to the FAISS index file.
    """

    def __init__(
        self,
        db: AsyncSession,
        index_path: str,
    ) -> None:
        self.db = db
        self.index_path = index_path
        self.index = None

        # Attempt to load the FAISS index if the file exists
        if faiss is None:
            logger.warning(
                "FAISS package not available. Running in fallback mode."
            )
            return

        if Path(index_path).exists():
            try:
                self.index = faiss.read_index(index_path)
                logger.info(
                    "FAISS index loaded: %s (%d vectors)",
                    index_path,
                    self.index.ntotal,
                )
            except Exception as exc:
                logger.error(
                    "Failed to load FAISS index from %s: %s. Running in fallback mode.",
                    index_path,
                    exc,
                )
                self.index = None
        else:
            # Index not present — create an empty one so it's ready when products are loaded.
            # Fallback DB retrieval will be used for searches until the index is populated.
            try:
                Path(index_path).parent.mkdir(parents=True, exist_ok=True)
                empty_index = faiss.IndexFlatL2(128)  # 128-dim default
                faiss.write_index(empty_index, index_path)
                self.index = None  # Leave None so DB fallback is used (index is empty)
                logger.info("Initialized empty product index at '%s'", index_path)
            except Exception:
                self.index = None
                logger.info(
                    "Product index not found at '%s' — using database retrieval.",
                    index_path,
                )

    async def retrieve(
        self,
        embedding: list[float],
        top_k: int = 20,
        category: str | None = None,
        situation: str | None = None,
    ) -> tuple[list, dict]:
        """Retrieve similar products using vector search.

        Args:
            embedding: Query embedding vector.
            top_k: Maximum number of results to return.
            category: Optional category for DB fallback.
            situation: Original user situation text for context-aware search.

        Returns:
            Tuple of (products, score_map).
            Falls back to DB category+situation search when FAISS is unavailable.
        """
        if self.index is None:
            logger.info("FAISS unavailable — using context-aware database retrieval.")
            return await self._fallback_retrieve(top_k, category, situation)

        try:
            query = np.array(
                [embedding],
                dtype="float32",
            )

            distances, ids = self.index.search(query, top_k)

            product_ids = ids[0].tolist()

            # Filter out -1 (FAISS returns -1 for unfilled slots)
            valid_ids = [pid for pid in product_ids if pid != -1]

            if not valid_ids:
                return await self._fallback_retrieve(top_k, category)

            stmt = select(Product).where(
                Product.id.in_(valid_ids)
            )

            result = await self.db.execute(stmt)
            products = list(result.scalars().all())

            score_map = {
                str(product_ids[i]): float(distances[0][i])
                for i in range(len(product_ids))
                if product_ids[i] != -1
            }

            logger.debug(
                "Retrieved %d products from FAISS (top_k=%d)",
                len(products),
                top_k,
            )

            return products, score_map

        except Exception as exc:
            logger.error("FAISS retrieval failed: %s. Using DB fallback.", exc)
            return await self._fallback_retrieve(top_k, category, situation)

    async def _fallback_retrieve(
        self,
        top_k: int = 20,
        category: str | None = None,
        situation: str | None = None,
    ) -> tuple[list, dict]:
        """Context-aware fallback: retrieve products by symptom/intent keywords."""
        try:
            from sqlalchemy import func, or_

            stmt = select(Product)

            # Build search keywords from BOTH category and situation
            keywords: list[str] = []
            if situation:
                situation_terms = self.situation_to_search_terms(situation)
                keywords.extend(situation_terms)

            if category and not keywords:
                keywords = self._category_to_keywords(category)

            if keywords:
                conditions = [Product.title.ilike(f"%{kw}%") for kw in keywords]
                stmt = stmt.where(or_(*conditions))

            # Prefer products with actual prices
            stmt = stmt.where(Product.price > 0).order_by(func.random()).limit(top_k)

            result = await self.db.execute(stmt)
            products = list(result.scalars().all())

            # If not enough products found, broaden search with category
            if len(products) < top_k and category and situation:
                cat_keywords = self._category_to_keywords(category)
                stmt2 = select(Product)
                conditions2 = [Product.title.ilike(f"%{kw}%") for kw in cat_keywords]
                existing_ids = {p.id for p in products}
                stmt2 = stmt2.where(or_(*conditions2)).where(Product.price > 0)
                stmt2 = stmt2.order_by(func.random()).limit(top_k - len(products))
                result2 = await self.db.execute(stmt2)
                extra = [p for p in result2.scalars().all() if p.id not in existing_ids]
                products.extend(extra)

            # Generate relevance scores (higher for situation-matched products)
            score_map = {}
            for i, p in enumerate(products):
                base_score = 0.95 - (i * 0.05)
                # Boost score if product title matches situation keywords
                if keywords:
                    title_lower = p.title.lower()
                    matches = sum(1 for kw in keywords if kw.lower() in title_lower)
                    base_score += matches * 0.1
                score_map[str(p.id)] = round(min(base_score, 1.0), 3)

            logger.info(
                "Context-aware retrieval: %d products (keywords=%s, category=%s)",
                len(products),
                keywords[:5] if keywords else "none",
                category or "any",
            )

            return products, score_map

        except Exception as exc:
            logger.error("DB fallback retrieval failed: %s", exc)
            return [], {}

    @staticmethod
    def _category_to_keywords(category: str) -> list[str]:
        """Map intent category to product title search keywords."""
        keyword_map = {
            "baby": ["baby", "infant", "formula", "diaper", "wipes", "newborn"],
            "medical": ["medicine", "tablet", "thermometer", "bandage", "first aid", "pain relief"],
            "groceries": ["milk", "bread", "rice", "oil", "butter", "egg"],
            "party": ["chips", "drink", "cup", "plate", "snack"],
            "cleaning": ["soap", "detergent", "cleaner", "mop", "brush"],
            "personal_care": ["shampoo", "lotion", "cream", "toothpaste", "sunscreen", "skin"],
            "vitamins": ["vitamin", "supplement", "omega", "calcium", "protein"],
            "hygiene": ["sanitizer", "mask", "tissue", "wash"],
            "electronics": ["charger", "cable", "battery", "light", "led"],
            "elderly_care": ["wheelchair", "cane", "adult diaper", "walker"],
            "first_aid": ["bandage", "antiseptic", "gauze", "medical tape", "cotton", "first aid", "wound"],
            "fever": ["thermometer", "paracetamol", "ors", "fever", "temperature"],
            "headache": ["pain relief", "ibuprofen", "paracetamol", "headache", "aspirin"],
            "cold_cough": ["tissue", "inhaler", "lozenge", "cough", "cold", "steam", "nasal"],
            "allergy": ["antihistamine", "allergy", "cetirizine"],
            "diabetes": ["insulin", "glucometer", "diabetic", "sugar free", "test strip"],
            "blood_pressure": ["blood pressure", "bp monitor", "hypertension"],
        }
        return keyword_map.get(category, [category])

    @staticmethod
    def situation_to_search_terms(situation: str) -> list[str]:
        """Extract search terms directly from the user's situation text.

        Maps symptoms/needs to specific product keywords for context-aware retrieval.
        """
        situation_lower = situation.lower()

        symptom_map = {
            "cut": ["bandage", "antiseptic", "gauze", "first aid"],
            "wound": ["bandage", "antiseptic", "gauze", "wound care"],
            "bleed": ["bandage", "gauze", "cotton", "first aid"],
            "finger": ["bandage", "antiseptic", "band aid"],
            "fever": ["thermometer", "paracetamol", "fever", "ors"],
            "headache": ["pain relief", "ibuprofen", "paracetamol"],
            "cold": ["tissue", "cold", "nasal", "steam inhaler"],
            "cough": ["cough syrup", "lozenge", "inhaler", "honey"],
            "sore throat": ["lozenge", "throat", "gargle"],
            "stomach": ["antacid", "ors", "digestive"],
            "diarrhea": ["ors", "electrolyte", "probiotic"],
            "allergy": ["antihistamine", "allergy", "cetirizine"],
            "rash": ["cream", "ointment", "calamine", "rash"],
            "burn": ["burn", "cream", "aloe", "ointment"],
            "sprain": ["pain relief", "bandage", "ice pack", "support"],
            "back pain": ["pain relief", "back", "muscle", "gel"],
            "eye": ["eye drop", "eye wash", "lens"],
            "ear": ["ear drop", "ear"],
            "diabetes": ["insulin", "glucometer", "test strip"],
            "blood pressure": ["bp monitor", "blood pressure"],
            "baby": ["baby formula", "diaper", "wipes", "baby"],
            "infant": ["infant formula", "baby", "newborn"],
            "diaper": ["diaper", "wipes", "rash cream"],
            "vitamin": ["vitamin", "supplement", "multivitamin"],
            "first aid": ["first aid", "bandage", "antiseptic", "gauze"],
        }

        matched: list[str] = []
        for symptom, terms in symptom_map.items():
            if symptom in situation_lower:
                matched.extend(terms)

        # Deduplicate preserving order
        seen: set[str] = set()
        result: list[str] = []
        for term in matched:
            if term not in seen:
                seen.add(term)
                result.append(term)

        return result
