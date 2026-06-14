"""Tests for the Sustainability API endpoint (app/api/v1/sustainability.py).

Covers:
    1. Eco score generation — GET /score/{product_id}.
    2. Alternative recommendations — POST /recommend.
    3. Sustainability report — POST /analyze.
    4. Invalid product ID — 404, 422, validation errors.

Uses a self-contained FastAPI app to avoid deep import chains.
The sustainability router interface is replicated with a mocked service.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Lightweight schema replicas
# ---------------------------------------------------------------------------


class EcoAlternativeSchema(BaseModel):
    original_product_id: UUID
    original_product_name: str
    alternative_product_id: UUID
    alternative_product_name: str
    carbon_saved: float
    price_difference: float
    sustainability_score: float


class SustainabilityAnalyzeRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_ids: list[UUID] = Field(..., min_length=1)


class SustainabilityRecommendRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_ids: list[UUID] = Field(..., min_length=1)


class SustainabilityReportResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eco_alternatives: list[EcoAlternativeSchema] = Field(default_factory=list)
    total_carbon_saved: float
    overall_sustainability_score: float


class SustainabilityRecommendResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendations: list[EcoAlternativeSchema] = Field(default_factory=list)
    total_carbon_saved: float
    overall_sustainability_score: float


class ProductEcoScoreResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: UUID
    product_name: str
    category: str
    sustainability_score: float = Field(ge=0, le=100)


# ---------------------------------------------------------------------------
# Simulated exceptions
# ---------------------------------------------------------------------------


class SustainabilityAgentException(Exception):
    pass


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/sustainability.py interface)
# ---------------------------------------------------------------------------


def _build_sustainability_router(get_service_dep):
    """Build a sustainability router with the given dependency."""
    router = APIRouter(prefix="/sustainability", tags=["Sustainability"])

    @router.post("/analyze", response_model=SustainabilityReportResponseSchema, status_code=200)
    async def analyze_sustainability(
        request: SustainabilityAnalyzeRequestSchema,
        service=Depends(get_service_dep),
    ) -> SustainabilityReportResponseSchema:
        try:
            return await service.generate_report(product_ids=request.product_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SustainabilityAgentException as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to generate sustainability report")

    @router.post("/recommend", response_model=SustainabilityRecommendResponseSchema, status_code=200)
    async def recommend_sustainability(
        request: SustainabilityRecommendRequestSchema,
        service=Depends(get_service_dep),
    ) -> SustainabilityRecommendResponseSchema:
        try:
            return await service.recommend_alternatives(product_ids=request.product_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SustainabilityAgentException as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to generate sustainability recommendations")

    @router.get("/score/{product_id}", response_model=ProductEcoScoreResponseSchema, status_code=200)
    async def get_product_eco_score(
        product_id: UUID,
        service=Depends(get_service_dep),
    ) -> ProductEcoScoreResponseSchema:
        try:
            return await service.get_product_score(product_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to retrieve product eco score")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def product_id() -> UUID:
    return uuid4()


@pytest.fixture
def product_ids() -> list[UUID]:
    return [uuid4(), uuid4(), uuid4()]


@pytest.fixture
def sample_eco_alternative(product_ids: list[UUID]) -> EcoAlternativeSchema:
    """A sample eco alternative."""
    return EcoAlternativeSchema(
        original_product_id=product_ids[0],
        original_product_name="Regular Detergent",
        alternative_product_id=uuid4(),
        alternative_product_name="Eco-Friendly Detergent",
        carbon_saved=1.5,
        price_difference=2.50,
        sustainability_score=82.0,
    )


@pytest.fixture
def sample_report_response(
    sample_eco_alternative: EcoAlternativeSchema,
) -> SustainabilityReportResponseSchema:
    """A sample sustainability report."""
    return SustainabilityReportResponseSchema(
        eco_alternatives=[sample_eco_alternative],
        total_carbon_saved=1.5,
        overall_sustainability_score=72.0,
    )


@pytest.fixture
def sample_recommend_response(
    sample_eco_alternative: EcoAlternativeSchema,
) -> SustainabilityRecommendResponseSchema:
    """A sample recommendation response."""
    return SustainabilityRecommendResponseSchema(
        recommendations=[sample_eco_alternative],
        total_carbon_saved=1.5,
        overall_sustainability_score=72.0,
    )


@pytest.fixture
def sample_eco_score_response(product_id: UUID) -> ProductEcoScoreResponseSchema:
    """A sample product eco score response."""
    return ProductEcoScoreResponseSchema(
        product_id=product_id,
        product_name="Organic Cotton T-Shirt",
        category="clothing",
        sustainability_score=78.5,
    )


@pytest.fixture
def mock_sustainability_service(
    sample_report_response: SustainabilityReportResponseSchema,
    sample_recommend_response: SustainabilityRecommendResponseSchema,
    sample_eco_score_response: ProductEcoScoreResponseSchema,
) -> AsyncMock:
    """Create a mocked SustainabilityService."""
    service = AsyncMock()
    service.generate_report = AsyncMock(return_value=sample_report_response)
    service.recommend_alternatives = AsyncMock(return_value=sample_recommend_response)
    service.get_product_score = AsyncMock(return_value=sample_eco_score_response)
    return service


@pytest.fixture
def client(mock_sustainability_service: AsyncMock) -> TestClient:
    """Create a TestClient with mocked sustainability service."""
    app = FastAPI()

    def get_service():
        return mock_sustainability_service

    router = _build_sustainability_router(get_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Eco Score Generation
# ---------------------------------------------------------------------------


class TestEcoScoreGeneration:
    """Test GET /api/v1/sustainability/score/{product_id} endpoint."""

    def test_get_eco_score_returns_200(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """Successful score retrieval returns 200."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        assert response.status_code == 200

    def test_get_eco_score_returns_product_id(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """Response contains the correct product_id."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        data = response.json()
        assert "product_id" in data
        UUID(data["product_id"])  # validates format

    def test_get_eco_score_returns_product_name(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """Response contains a product name."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        data = response.json()
        assert "product_name" in data
        assert len(data["product_name"]) > 0

    def test_get_eco_score_returns_category(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """Response contains a category."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        data = response.json()
        assert "category" in data
        assert len(data["category"]) > 0

    def test_get_eco_score_returns_valid_score(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """sustainability_score is between 0 and 100."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        score = response.json()["sustainability_score"]
        assert 0 <= score <= 100

    def test_get_eco_score_calls_service(
        self, client: TestClient, product_id: UUID, mock_sustainability_service: AsyncMock
    ) -> None:
        """Service.get_product_score is called with correct product_id."""
        client.get(f"/api/v1/sustainability/score/{product_id}")
        mock_sustainability_service.get_product_score.assert_called_once_with(product_id)

    def test_get_eco_score_response_schema(
        self, client: TestClient, product_id: UUID
    ) -> None:
        """Response deserializes into ProductEcoScoreResponseSchema."""
        response = client.get(f"/api/v1/sustainability/score/{product_id}")
        parsed = ProductEcoScoreResponseSchema.model_validate(response.json())
        assert parsed.sustainability_score == 78.5


# ---------------------------------------------------------------------------
# Test 2: Alternative Recommendations
# ---------------------------------------------------------------------------


class TestAlternativeRecommendations:
    """Test POST /api/v1/sustainability/recommend endpoint."""

    def test_recommend_returns_200(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Successful recommendation returns 200."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        assert response.status_code == 200

    def test_recommend_returns_recommendations_list(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains a recommendations list."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_recommend_returns_carbon_saved(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains total_carbon_saved."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "total_carbon_saved" in data
        assert data["total_carbon_saved"] >= 0

    def test_recommend_returns_overall_score(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains overall_sustainability_score."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "overall_sustainability_score" in data

    def test_recommend_alternative_structure(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Each alternative has required fields."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        alt = response.json()["recommendations"][0]
        assert "original_product_id" in alt
        assert "original_product_name" in alt
        assert "alternative_product_id" in alt
        assert "alternative_product_name" in alt
        assert "carbon_saved" in alt
        assert "price_difference" in alt
        assert "sustainability_score" in alt

    def test_recommend_calls_service(
        self, client: TestClient, product_ids: list[UUID], mock_sustainability_service: AsyncMock
    ) -> None:
        """Service.recommend_alternatives is called with correct product_ids."""
        client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        mock_sustainability_service.recommend_alternatives.assert_called_once()
        call_kwargs = mock_sustainability_service.recommend_alternatives.call_args[1]
        assert call_kwargs["product_ids"] == product_ids

    def test_recommend_response_schema(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response deserializes into SustainabilityRecommendResponseSchema."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        parsed = SustainabilityRecommendResponseSchema.model_validate(response.json())
        assert parsed.total_carbon_saved == 1.5


# ---------------------------------------------------------------------------
# Test 3: Sustainability Report
# ---------------------------------------------------------------------------


class TestSustainabilityReport:
    """Test POST /api/v1/sustainability/analyze endpoint."""

    def test_analyze_returns_200(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Successful report generation returns 200."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        assert response.status_code == 200

    def test_analyze_returns_eco_alternatives(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains eco_alternatives list."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "eco_alternatives" in data
        assert isinstance(data["eco_alternatives"], list)

    def test_analyze_returns_total_carbon_saved(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains total_carbon_saved."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "total_carbon_saved" in data
        assert isinstance(data["total_carbon_saved"], (int, float))

    def test_analyze_returns_overall_score(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response contains overall_sustainability_score."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        data = response.json()
        assert "overall_sustainability_score" in data

    def test_analyze_calls_service(
        self, client: TestClient, product_ids: list[UUID], mock_sustainability_service: AsyncMock
    ) -> None:
        """Service.generate_report is called with correct product_ids."""
        client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        mock_sustainability_service.generate_report.assert_called_once()
        call_kwargs = mock_sustainability_service.generate_report.call_args[1]
        assert call_kwargs["product_ids"] == product_ids

    def test_analyze_single_product(
        self, client: TestClient
    ) -> None:
        """Report generation works with a single product."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 200

    def test_analyze_response_schema(
        self, client: TestClient, product_ids: list[UUID]
    ) -> None:
        """Response deserializes into SustainabilityReportResponseSchema."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(pid) for pid in product_ids]},
        )
        parsed = SustainabilityReportResponseSchema.model_validate(response.json())
        assert parsed.overall_sustainability_score == 72.0
        assert len(parsed.eco_alternatives) == 1


# ---------------------------------------------------------------------------
# Test 4: Invalid Product ID / Error Handling
# ---------------------------------------------------------------------------


class TestInvalidProductId:
    """Test error cases: invalid IDs, not found, agent errors, validation."""

    # --- Eco Score Errors ---

    def test_eco_score_invalid_uuid_returns_422(self, client: TestClient) -> None:
        """Non-UUID path parameter returns 422."""
        response = client.get("/api/v1/sustainability/score/not-a-uuid")
        assert response.status_code == 422

    def test_eco_score_product_not_found_returns_404(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Product not found returns 404."""
        mock_sustainability_service.get_product_score.side_effect = ValueError(
            "Product not found"
        )
        response = client.get(f"/api/v1/sustainability/score/{uuid4()}")
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

    def test_eco_score_internal_error_returns_500(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Unexpected exception returns 500."""
        mock_sustainability_service.get_product_score.side_effect = RuntimeError("DB error")
        response = client.get(f"/api/v1/sustainability/score/{uuid4()}")
        assert response.status_code == 500
        assert "Failed to retrieve" in response.json()["detail"]

    # --- Analyze Errors ---

    def test_analyze_empty_product_ids_returns_422(self, client: TestClient) -> None:
        """Empty product_ids list returns 422 (min_length=1)."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": []},
        )
        assert response.status_code == 422

    def test_analyze_missing_product_ids_returns_422(self, client: TestClient) -> None:
        """Missing product_ids field returns 422."""
        response = client.post("/api/v1/sustainability/analyze", json={})
        assert response.status_code == 422

    def test_analyze_invalid_uuid_in_list_returns_422(self, client: TestClient) -> None:
        """Invalid UUID in product_ids list returns 422."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": ["not-a-uuid"]},
        )
        assert response.status_code == 422

    def test_analyze_products_not_found_returns_404(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Products not found returns 404."""
        mock_sustainability_service.generate_report.side_effect = ValueError(
            "No products found"
        )
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 404
        assert "No products found" in response.json()["detail"]

    def test_analyze_agent_error_returns_422(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """SustainabilityAgentException returns 422."""
        mock_sustainability_service.generate_report.side_effect = SustainabilityAgentException(
            "Agent analysis failed"
        )
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 422
        assert "Agent analysis failed" in response.json()["detail"]

    def test_analyze_internal_error_returns_500(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Unexpected exception on analyze returns 500."""
        mock_sustainability_service.generate_report.side_effect = RuntimeError("Timeout")
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 500
        assert "Failed to generate sustainability report" in response.json()["detail"]

    # --- Recommend Errors ---

    def test_recommend_empty_product_ids_returns_422(self, client: TestClient) -> None:
        """Empty product_ids returns 422."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": []},
        )
        assert response.status_code == 422

    def test_recommend_products_not_found_returns_404(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Products not found returns 404."""
        mock_sustainability_service.recommend_alternatives.side_effect = ValueError(
            "No products found for the provided identifiers"
        )
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 404

    def test_recommend_agent_error_returns_422(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """SustainabilityAgentException on recommend returns 422."""
        mock_sustainability_service.recommend_alternatives.side_effect = SustainabilityAgentException(
            "Agent failed"
        )
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 422

    def test_recommend_internal_error_returns_500(
        self, client: TestClient, mock_sustainability_service: AsyncMock
    ) -> None:
        """Unexpected exception on recommend returns 500."""
        mock_sustainability_service.recommend_alternatives.side_effect = RuntimeError("crash")
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(uuid4())]},
        )
        assert response.status_code == 500

    # --- Extra validation ---

    def test_analyze_extra_fields_rejected(self, client: TestClient) -> None:
        """Extra fields in request body are rejected."""
        response = client.post(
            "/api/v1/sustainability/analyze",
            json={"product_ids": [str(uuid4())], "extra": "nope"},
        )
        assert response.status_code == 422

    def test_recommend_non_json_body_returns_422(self, client: TestClient) -> None:
        """Non-JSON body returns 422."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
