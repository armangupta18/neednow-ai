from fastapi import APIRouter

router = APIRouter()

@router.get("/chat-test")
async def chat_test():
    return {
        "message": "chat api working"
    }