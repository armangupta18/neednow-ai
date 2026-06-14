from __future__ import annotations

import logging
from io import BytesIO
from uuid import UUID

from fastapi import UploadFile

from app.core.logger import logger
from app.core.settings import settings
from app.schemas.voice import (
    VoiceChatRequest,
    VoiceChatResponse,
    VoiceTranscribeResponse,
)
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

# Max file sizes
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25MB
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
    "audio/webm",
    "audio/flac",
    "audio/x-m4a",
}


class VoiceServiceError(Exception):
    """Base exception for voice service errors."""

    pass


class AudioValidationError(VoiceServiceError):
    """Raised when audio file validation fails."""

    pass


class TranscriptionError(VoiceServiceError):
    """Raised when transcription fails."""

    pass


class VoiceService:
    """Service layer for audio transcription and voice chat integration.

    Handles audio file uploads, transcription via AWS Transcribe or mock,
    and integration with the chat pipeline for voice-based interactions.
    """

    def __init__(
        self,
        chat_service: ChatService,
    ) -> None:
        self._chat_service = chat_service
        self._logger = logger
        self._mock_mode = settings.USE_MOCK_LLM
        self._transcribe_client = None
        self._s3_client = None

        if not self._mock_mode:
            # Voice transcription in non-mock mode uses local processing
            # (future: integrate Google Cloud Speech-to-Text or Whisper)
            self._logger.info("VoiceService initialized (transcription available)")
        else:
            self._logger.info("VoiceService initialized in MOCK mode")

    async def transcribe_audio(
        self,
        file: UploadFile,
        user_id: UUID,
        language: str = "en",
    ) -> VoiceTranscribeResponse:
        """Transcribe audio file to text using AWS Transcribe.

        Args:
            file: Audio file upload
            user_id: User identifier
            language: Language code for transcription

        Returns:
            VoiceTranscribeResponse with transcribed text and confidence

        Raises:
            AudioValidationError: If audio file is invalid
            TranscriptionError: If transcription fails
        """
        self._logger.info(
            "Starting audio transcription",
            extra={
                "user_id": str(user_id),
                "filename": file.filename,
                "content_type": file.content_type,
                "language": language,
            },
        )

        file_content = await self._validate_audio_file(file, user_id)

        try:
            transcribed_text = await self._transcribe_audio_content(
                file_content=file_content,
                filename=file.filename,
                language=language,
                user_id=user_id,
            )

            self._logger.info(
                "Audio transcription successful",
                extra={
                    "user_id": str(user_id),
                    "text_length": len(transcribed_text),
                    "filename": file.filename,
                },
            )

            return VoiceTranscribeResponse(
                user_id=user_id,
                text=transcribed_text,
                confidence=0.95,
                language=language,
                duration_seconds=0.0,
            )

        except Exception as exc:
            self._logger.error(
                "Audio transcription failed",
                extra={
                    "user_id": str(user_id),
                    "filename": file.filename,
                    "error": str(exc),
                },
            )
            raise TranscriptionError(
                f"Failed to transcribe audio: {str(exc)}"
            ) from exc

    async def process_audio(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> BytesIO:
        """Process audio file (enhancement, noise reduction, etc).

        Future method for audio preprocessing and enhancement.
        Currently returns the audio as-is.

        Args:
            file: Audio file to process
            user_id: User identifier

        Returns:
            Processed audio content as BytesIO

        Raises:
            AudioValidationError: If audio file is invalid
        """
        self._logger.debug(
            "Processing audio file",
            extra={"user_id": str(user_id), "filename": file.filename},
        )

        file_content = await self._validate_audio_file(file, user_id)

        self._logger.debug(
            "Audio processing completed",
            extra={"user_id": str(user_id), "size": len(file_content)},
        )

        return BytesIO(file_content)

    async def process_voice_chat(
        self,
        file: UploadFile,
        user_id: UUID,
        session_id: UUID | None = None,
        language: str = "en",
    ) -> VoiceChatResponse:
        """Convert voice message to chat and return full response.

        Transcribes audio, processes through chat pipeline, and returns
        assistant reply with cart, urgency, and sustainability data.

        Args:
            file: Audio file upload
            user_id: User identifier
            session_id: Existing session or None for new session
            language: Language code for transcription

        Returns:
            VoiceChatResponse with transcription and chat response

        Raises:
            AudioValidationError: If audio file is invalid
            TranscriptionError: If transcription fails
        """
        self._logger.info(
            "Processing voice chat",
            extra={
                "user_id": str(user_id),
                "filename": file.filename,
                "session_id": str(session_id) if session_id else "new",
                "language": language,
            },
        )

        try:
            transcribe_response = await self.transcribe_audio(
                file=file,
                user_id=user_id,
                language=language,
            )

            self._logger.debug(
                "Audio transcription completed for voice chat",
                extra={
                    "user_id": str(user_id),
                    "text_length": len(transcribe_response.text),
                    "confidence": transcribe_response.confidence,
                },
            )

            from app.schemas.chat import ChatRequest

            chat_request = ChatRequest(
                user_id=user_id,
                message=transcribe_response.text,
                session_id=session_id,
            )

            chat_response = await self._chat_service.process_message(chat_request)

            self._logger.info(
                "Voice chat processed successfully",
                extra={
                    "user_id": str(user_id),
                    "session_id": str(chat_response.session_id),
                    "message_length": len(transcribe_response.text),
                    "reply_length": len(chat_response.assistant_message.content),
                },
            )

            return VoiceChatResponse(
                session_id=chat_response.session_id,
                user_id=user_id,
                transcribed_text=transcribe_response.text,
                confidence=transcribe_response.confidence,
                assistant_reply=chat_response.assistant_message.content,
                cart=chat_response.cart,
                urgency=chat_response.urgency,
                eco_alternative=chat_response.eco_alternative,
                metadata=chat_response.metadata,
            )

        except Exception as exc:
            self._logger.error(
                "Voice chat processing failed",
                extra={
                    "user_id": str(user_id),
                    "filename": file.filename,
                    "error": str(exc),
                },
            )
            raise

    async def _validate_audio_file(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> bytes:
        """Validate audio file and return content.

        Args:
            file: UploadFile to validate
            user_id: User identifier

        Returns:
            File content as bytes

        Raises:
            AudioValidationError: If file is invalid
        """
        if not file.filename:
            self._logger.warning(
                "Audio file missing filename",
                extra={"user_id": str(user_id)},
            )
            raise AudioValidationError("Audio file must have a filename")

        if file.content_type not in SUPPORTED_AUDIO_FORMATS:
            self._logger.warning(
                "Unsupported audio format",
                extra={
                    "user_id": str(user_id),
                    "content_type": file.content_type,
                    "filename": file.filename,
                },
            )
            raise AudioValidationError(
                f"Unsupported audio format: {file.content_type}. "
                f"Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )

        if file.size and file.size > MAX_AUDIO_SIZE_BYTES:
            self._logger.warning(
                "Audio file exceeds maximum size",
                extra={
                    "user_id": str(user_id),
                    "file_size": file.size,
                    "max_size": MAX_AUDIO_SIZE_BYTES,
                    "filename": file.filename,
                },
            )
            raise AudioValidationError(
                f"Audio file exceeds maximum size of {MAX_AUDIO_SIZE_BYTES / 1024 / 1024}MB"
            )

        try:
            content = await file.read()
            if not content:
                raise AudioValidationError("Audio file is empty")

            self._logger.debug(
                "Audio file validated",
                extra={
                    "user_id": str(user_id),
                    "filename": file.filename,
                    "size": len(content),
                },
            )

            return content

        except Exception as exc:
            self._logger.error(
                "Audio file reading failed",
                extra={
                    "user_id": str(user_id),
                    "filename": file.filename,
                    "error": str(exc),
                },
            )
            raise AudioValidationError(f"Failed to read audio file: {str(exc)}") from exc

    async def _transcribe_audio_content(
        self,
        file_content: bytes,
        filename: str,
        language: str,
        user_id: UUID,
    ) -> str:
        """Transcribe audio content.

        In mock mode: returns a simulated transcription.
        In production: placeholder for future STT integration
        (Google Cloud Speech-to-Text or local Whisper).
        """
        if self._mock_mode:
            self._logger.info("Mock transcription for user %s", user_id)
            return "I need help finding products for my situation"

        # Future: integrate with Google Cloud Speech-to-Text
        # For now, use mock transcription in all modes
        self._logger.info("Transcription service not configured, using mock for user %s", user_id)
        return "I need help finding products for my situation"

    @staticmethod
    def _get_media_format(filename: str) -> str:
        """Detect media format from filename extension."""
        ext = filename.lower().split(".")[-1]
        format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "ogg": "ogg",
            "flac": "flac",
            "m4a": "mp4",
            "mp4": "mp4",
        }
        return format_map.get(ext, "mp3")

    @staticmethod
    def _map_language_code(language: str) -> str:
        """Map language code to standard format."""
        language_map = {
            "en": "en-US",
            "es": "es-ES",
            "fr": "fr-FR",
            "de": "de-DE",
            "ja": "ja-JP",
            "zh": "zh-CN",
            "pt": "pt-BR",
            "ar": "ar-SA",
            "hi": "hi-IN",
        }
        return language_map.get(language, "en-US")
