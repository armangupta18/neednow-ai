from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.chat_service import ChatService
from app.services.voice_service import VoiceService


def get_voice_service(
    db: AsyncSession = Depends(get_db),
) -> VoiceService:
    from app.dependencies.chat import get_chat_service

    chat_service = get_chat_service(db)
    return VoiceService(chat_service=chat_service)
