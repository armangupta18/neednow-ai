"""Schemas package for NeedNow AI.

Exports all Pydantic request/response models used across API endpoints.
"""

from app.schemas.cart import (
    CartAddRequest,
    CartClearResponse,
    CartItemResponse,
    CartMutationResponse,
    CartRemoveRequest,
    CartResponse,
)
from app.schemas.chat import (
    CartSnapshot,
    ChatEventType,
    ChatHistoryRequest,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
    EcoAlternative,
    UrgencySnapshot,
)
from app.schemas.emergency import (
    EmergencyAnalyzeRequest,
    EmergencyAnalyzeResponse,
    EmergencyEscalateRequest,
    EmergencyEscalateResponse,
    EmergencyHealthResponse,
)
from app.schemas.intent import (
    IntentRequest,
)
from app.schemas.memory import (
    ClearMemoryResponse,
    MemoryResponse,
    StoreMemoryRequest,
)
from app.schemas.recommendation import (
    RecommendationBase,
    RecommendationCreate,
    RecommendationListResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.sustainability import (
    ProductEcoScoreResponse,
    SustainabilityAnalyzeRequest,
    SustainabilityRecommendRequest,
    SustainabilityRecommendResponse,
    SustainabilityReportResponse,
)
from app.schemas.voice import (
    VoiceChatRequest,
    VoiceChatResponse,
    VoiceTranscribeResponse,
)

__all__: list[str] = [
    # Cart
    "CartAddRequest",
    "CartClearResponse",
    "CartItemResponse",
    "CartMutationResponse",
    "CartRemoveRequest",
    "CartResponse",
    # Chat
    "CartSnapshot",
    "ChatEventType",
    "ChatHistoryRequest",
    "ChatHistoryResponse",
    "ChatRequest",
    "ChatResponse",
    "ChatStreamEvent",
    "EcoAlternative",
    "UrgencySnapshot",
    # Emergency
    "EmergencyAnalyzeRequest",
    "EmergencyAnalyzeResponse",
    "EmergencyEscalateRequest",
    "EmergencyEscalateResponse",
    "EmergencyHealthResponse",
    # Intent
    "IntentRequest",
    # Memory
    "ClearMemoryResponse",
    "MemoryResponse",
    "StoreMemoryRequest",
    # Recommendation
    "RecommendationBase",
    "RecommendationCreate",
    "RecommendationListResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    # Sustainability
    "ProductEcoScoreResponse",
    "SustainabilityAnalyzeRequest",
    "SustainabilityRecommendRequest",
    "SustainabilityRecommendResponse",
    "SustainabilityReportResponse",
    # Voice
    "VoiceChatRequest",
    "VoiceChatResponse",
    "VoiceTranscribeResponse",
]
