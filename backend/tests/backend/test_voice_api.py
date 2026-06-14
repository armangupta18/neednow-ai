"""Tests for the Voice API endpoint (app/api/v1/voice.py).

Covers:
    1. Audio upload — successful file upload and transcription.
    2. Audio transcription — response structure and content.
    3. Invalid file — missing file, wrong format, oversized.
    4. Service failure — error handling and status codes.

Uses a self-contained FastAPI app to avoid deep import chains.
The voice router interface is replicated with a mocked VoiceService.
"""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Lightweight schema replicas
# ---------------------------------------------------------------------------


class VoiceTranscribeResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    language: str = "en"
    duration_seconds: float = 0.0


class VoiceChatRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    session_id: UUID | None = None
    language: str = "en"


class VoiceChatResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    user_id: UUID
    transcribed_text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    assistant_reply: str
    cart: dict = Field(default_factory=dict)
    urgency: dict | None = None
    eco_alternative: dict | None = None
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/voice.py interface)
# ---------------------------------------------------------------------------


def _build_voice_router(get_service_dep):
    """Build a voice router with the given dependency."""
    router = APIRouter(prefix="/voice", tags=["Voice"])

    @router.post("/transcribe", response_model=VoiceTranscribeResponseSchema, status_code=200)
    async def transcribe_audio(
        file: UploadFile = File(...),
        user_id: UUID = Query(...),
        language: str = Query("en"),
        voice_service=Depends(get_service_dep),
    ) -> VoiceTranscribeResponseSchema:
        try:
            if not file.filename:
                raise ValueError("File must have a filename")

            if file.size and file.size > 25 * 1024 * 1024:
                raise ValueError("File size must not exceed 25MB")

            return await voice_service.transcribe_audio(
                file=file,
                user_id=user_id,
                language=language,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio file")

    @router.post("/chat", response_model=VoiceChatResponseSchema, status_code=200)
    async def send_voice_chat(
        file: UploadFile = File(...),
        user_id: UUID = Query(...),
        session_id: UUID | None = Query(None),
        language: str = Query("en"),
        voice_service=Depends(get_service_dep),
    ) -> VoiceChatResponseSchema:
        try:
            if not file.filename:
                raise ValueError("File must have a filename")

            if file.size and file.size > 25 * 1024 * 1024:
                raise ValueError("File size must not exceed 25MB")

            return await voice_service.process_voice_chat(
                file=file,
                user_id=user_id,
                session_id=session_id,
                language=language,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to process voice chat message")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def session_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_transcribe_response(user_id: UUID) -> VoiceTranscribeResponseSchema:
    """Sample transcription response."""
    return VoiceTranscribeResponseSchema(
        user_id=user_id,
        text="I need baby formula urgently for my infant",
        confidence=0.94,
        language="en",
        duration_seconds=3.5,
    )


@pytest.fixture
def sample_voice_chat_response(user_id: UUID, session_id: UUID) -> VoiceChatResponseSchema:
    """Sample voice chat response."""
    return VoiceChatResponseSchema(
        session_id=session_id,
        user_id=user_id,
        transcribed_text="I need baby formula urgently for my infant",
        confidence=0.94,
        assistant_reply="I found several baby formula options available for immediate delivery.",
        cart={"cart_id": str(uuid4()), "total_amount": 0.0, "items": []},
        urgency={"level": "HIGH", "score": 82},
        eco_alternative={"product_name": "Organic Formula", "eco_score": 75.0},
        metadata={"pipeline_time_ms": 320.5},
    )


@pytest.fixture
def mock_voice_service(
    sample_transcribe_response: VoiceTranscribeResponseSchema,
    sample_voice_chat_response: VoiceChatResponseSchema,
) -> AsyncMock:
    """Create a mocked VoiceService."""
    service = AsyncMock()
    service.transcribe_audio = AsyncMock(return_value=sample_transcribe_response)
    service.process_voice_chat = AsyncMock(return_value=sample_voice_chat_response)
    return service


@pytest.fixture
def client(mock_voice_service: AsyncMock) -> TestClient:
    """Create a TestClient with the mocked voice service."""
    app = FastAPI()

    def get_service():
        return mock_voice_service

    router = _build_voice_router(get_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


@pytest.fixture
def audio_file() -> tuple[str, io.BytesIO, str]:
    """Fake audio file for upload tests."""
    content = b"\x00" * 1024  # 1KB of null bytes simulating audio
    return ("test_audio.wav", io.BytesIO(content), "audio/wav")


# ---------------------------------------------------------------------------
# Test 1: Audio Upload
# ---------------------------------------------------------------------------


class TestAudioUpload:
    """Test audio file upload via POST /api/v1/voice/transcribe."""

    def test_upload_audio_returns_200(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Successful audio upload returns 200."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 200

    def test_upload_audio_with_language(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Language parameter is accepted."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id), "language": "es"},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 200

    def test_upload_audio_calls_service(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """VoiceService.transcribe_audio is called."""
        filename, content, content_type = audio_file
        client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id), "language": "en"},
            files={"file": (filename, content, content_type)},
        )
        mock_voice_service.transcribe_audio.assert_called_once()

    def test_upload_various_audio_formats(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Various audio formats are accepted at the API level."""
        for fmt, mime in [("test.mp3", "audio/mpeg"), ("test.m4a", "audio/mp4"), ("test.webm", "audio/webm")]:
            content = io.BytesIO(b"\x00" * 512)
            response = client.post(
                "/api/v1/voice/transcribe",
                params={"user_id": str(user_id)},
                files={"file": (fmt, content, mime)},
            )
            assert response.status_code == 200

    def test_voice_chat_upload_returns_200(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat upload returns 200."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 200

    def test_voice_chat_with_session_id(
        self, client: TestClient, user_id: UUID, session_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat accepts an existing session_id."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id), "session_id": str(session_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: Audio Transcription
# ---------------------------------------------------------------------------


class TestAudioTranscription:
    """Test transcription response structure and content."""

    def test_transcribe_returns_text(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response contains transcribed text."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        data = response.json()
        assert "text" in data
        assert len(data["text"]) > 0

    def test_transcribe_returns_confidence(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response contains confidence score between 0 and 1."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        confidence = response.json()["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_transcribe_returns_user_id(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response contains the correct user_id."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.json()["user_id"] == str(user_id)

    def test_transcribe_returns_language(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response contains detected language."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert "language" in response.json()

    def test_transcribe_returns_duration(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response contains audio duration."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert "duration_seconds" in response.json()
        assert response.json()["duration_seconds"] >= 0

    def test_transcribe_response_schema(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response deserializes into VoiceTranscribeResponseSchema."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        parsed = VoiceTranscribeResponseSchema.model_validate(response.json())
        assert parsed.confidence == 0.94

    def test_voice_chat_returns_transcribed_text(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat response contains transcribed_text."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        data = response.json()
        assert "transcribed_text" in data
        assert len(data["transcribed_text"]) > 0

    def test_voice_chat_returns_assistant_reply(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat response contains assistant_reply."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        data = response.json()
        assert "assistant_reply" in data
        assert len(data["assistant_reply"]) > 0

    def test_voice_chat_returns_session_id(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat response contains a session_id."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        UUID(response.json()["session_id"])  # validates format

    def test_voice_chat_returns_urgency(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Voice chat response contains urgency data."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        urgency = response.json()["urgency"]
        assert urgency is not None
        assert "level" in urgency

    def test_voice_chat_response_schema(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Response deserializes into VoiceChatResponseSchema."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        parsed = VoiceChatResponseSchema.model_validate(response.json())
        assert parsed.confidence == 0.94
        assert parsed.assistant_reply != ""


# ---------------------------------------------------------------------------
# Test 3: Invalid File
# ---------------------------------------------------------------------------


class TestInvalidFile:
    """Test invalid file scenarios."""

    def test_transcribe_missing_file_returns_422(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Missing file returns 422."""
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
        )
        assert response.status_code == 422

    def test_transcribe_missing_user_id_returns_422(
        self, client: TestClient, audio_file: tuple
    ) -> None:
        """Missing user_id query param returns 422."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 422

    def test_transcribe_invalid_user_id_returns_422(
        self, client: TestClient, audio_file: tuple
    ) -> None:
        """Non-UUID user_id returns 422."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": "not-a-uuid"},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 422

    def test_voice_chat_missing_file_returns_422(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Voice chat without file returns 422."""
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
        )
        assert response.status_code == 422

    def test_voice_chat_invalid_session_id_returns_422(
        self, client: TestClient, user_id: UUID, audio_file: tuple
    ) -> None:
        """Invalid session_id format returns 422."""
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id), "session_id": "bad-uuid"},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 422

    def test_transcribe_validation_error_from_service(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """ValueError from service returns 400 (e.g., unsupported format)."""
        mock_voice_service.transcribe_audio.side_effect = ValueError(
            "Unsupported audio format"
        )
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 400
        assert "Unsupported audio format" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 4: Service Failure
# ---------------------------------------------------------------------------


class TestServiceFailure:
    """Test error handling for service-layer exceptions."""

    def test_transcribe_internal_error_returns_500(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """Unexpected exception on transcribe returns 500."""
        mock_voice_service.transcribe_audio.side_effect = RuntimeError("Whisper crashed")
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 500
        assert "Failed to transcribe" in response.json()["detail"]

    def test_transcribe_permission_error_returns_403(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """PermissionError returns 403."""
        mock_voice_service.transcribe_audio.side_effect = PermissionError("Quota exceeded")
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/transcribe",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 403
        assert "Quota exceeded" in response.json()["detail"]

    def test_voice_chat_internal_error_returns_500(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """Unexpected exception on voice chat returns 500."""
        mock_voice_service.process_voice_chat.side_effect = RuntimeError("Pipeline down")
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 500
        assert "Failed to process voice chat" in response.json()["detail"]

    def test_voice_chat_value_error_returns_400(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """ValueError on voice chat returns 400."""
        mock_voice_service.process_voice_chat.side_effect = ValueError("Audio too short")
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 400
        assert "Audio too short" in response.json()["detail"]

    def test_voice_chat_permission_error_returns_403(
        self,
        client: TestClient,
        user_id: UUID,
        audio_file: tuple,
        mock_voice_service: AsyncMock,
    ) -> None:
        """PermissionError on voice chat returns 403."""
        mock_voice_service.process_voice_chat.side_effect = PermissionError("Not authorized")
        filename, content, content_type = audio_file
        response = client.post(
            "/api/v1/voice/chat",
            params={"user_id": str(user_id)},
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
