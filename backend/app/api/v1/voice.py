from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.logger import logger
from app.dependencies.voice import get_voice_service
from app.schemas.voice import (
    VoiceChatRequest,
    VoiceChatResponse,
    VoiceTranscribeResponse,
)
from app.services.voice_service import VoiceService

router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


@router.post(
    "/transcribe",
    response_model=VoiceTranscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio file to text",
    description=(
        "Upload an audio file and transcribe it to text using "
        "Whisper-compatible transcription engine."
    ),
)
async def transcribe_audio(
    file: UploadFile = File(...),
    user_id: UUID = Query(..., description="User identifier"),
    language: str = Query("en", description="Language code (e.g., 'en', 'es')"),
    voice_service: VoiceService = Depends(get_voice_service),
) -> VoiceTranscribeResponse:
    try:
        if not file.filename:
            raise ValueError("File must have a filename")

        if file.size and file.size > 25 * 1024 * 1024:
            raise ValueError("File size must not exceed 25MB")

        logger.info(
            "Audio transcription started",
            extra={
                "user_id": str(user_id),
                "filename": file.filename,
                "content_type": file.content_type,
                "language": language,
            },
        )

        response = await voice_service.transcribe_audio(
            file=file,
            user_id=user_id,
            language=language,
        )

        logger.info(
            "Audio transcription completed",
            extra={
                "user_id": str(user_id),
                "text_length": len(response.text),
                "confidence": response.confidence,
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Voice transcribe validation error",
            extra={"user_id": str(user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        logger.warning(
            "Voice transcribe authorization error",
            extra={"user_id": str(user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Audio transcription failed",
            extra={"user_id": str(user_id), "filename": file.filename},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio file",
        )


@router.post(
    "/chat",
    response_model=VoiceChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send voice message through chat pipeline",
    description=(
        "Upload an audio file, transcribe it, and process through the chat pipeline "
        "to return assistant reply with cart, urgency, and sustainability data."
    ),
)
async def send_voice_chat(
    file: UploadFile = File(...),
    request: VoiceChatRequest = Depends(),
    voice_service: VoiceService = Depends(get_voice_service),
) -> VoiceChatResponse:
    try:
        if not file.filename:
            raise ValueError("File must have a filename")

        if file.size and file.size > 25 * 1024 * 1024:
            raise ValueError("File size must not exceed 25MB")

        logger.info(
            "Voice chat started",
            extra={
                "user_id": str(request.user_id),
                "filename": file.filename,
                "content_type": file.content_type,
                "session_id": str(request.session_id) if request.session_id else None,
            },
        )

        response = await voice_service.process_voice_chat(
            file=file,
            user_id=request.user_id,
            session_id=request.session_id,
            language=request.language,
        )

        logger.info(
            "Voice chat completed",
            extra={
                "user_id": str(request.user_id),
                "session_id": str(response.session_id),
                "text_length": len(response.transcribed_text),
                "urgency": response.urgency.get("level") if response.urgency else None,
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Voice chat validation error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        logger.warning(
            "Voice chat authorization error",
            extra={"user_id": str(request.user_id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Voice chat pipeline failed",
            extra={"user_id": str(request.user_id), "filename": file.filename},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice chat message",
        )
