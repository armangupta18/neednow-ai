from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.core.logger import logger
from app.core.exception import (
    NeedNowException,
    ValidationException,
    neednow_exception_handler,
    validation_exception_handler,
)
from app.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NeedNow AI Backend...")
    llm_mode = "MOCK" if settings.USE_MOCK_LLM else "GEMINI LIVE"
    has_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    logger.info("LLM Provider: Google Gemini (%s)", settings.GEMINI_MODEL_ID)
    logger.info("LLM Mode: %s | API Key: %s", llm_mode, "configured" if has_key else "missing")
    await init_db()
    logger.info("Database tables initialized.")
    print("\n" + "=" * 50)
    print("  NeedNow AI Backend Started")
    print(f"  LLM: Google Gemini ({settings.GEMINI_MODEL_ID})")
    print(f"  Mode: {llm_mode}")
    print(f"  API Key: {'✓ configured' if has_key else '✗ missing (mock mode)'}")
    print("=" * 50 + "\n")
    yield
    logger.info("Shutting down NeedNow AI Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NeedNow AI Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers (ValidationException first — more specific)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(NeedNowException, neednow_exception_handler)

from app.api.v1.intent import (
    router as intent_router
)
from app.api.v1.chat import router as chat_router
from app.api.v1.cart import router as cart_router
from app.api.v1.memory import router as memory_router
from app.api.v1.emergency import router as emergency_router
from app.api.v1.voice import router as voice_router
from app.api.v1.sustainability import router as sustainability_router
from app.api.v1.orders import router as orders_router

app.include_router(
    intent_router,
    prefix="/api/v1",
)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(emergency_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(sustainability_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
        },
    )