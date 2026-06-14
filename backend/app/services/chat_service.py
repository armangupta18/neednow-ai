from __future__ import annotations

import logging
from uuid import UUID, uuid4

from app.agents.shared.message import AgentMessage, MessageRole
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.exception import SupervisorException
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.cart_service import CartService

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates conversational chat turns through the supervisor pipeline."""

    def __init__(self, supervisor: SupervisorAgent) -> None:
        self._supervisor = supervisor
        self._sessions: dict[UUID, list[AgentMessage]] = {}

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or uuid4()

        user_message = AgentMessage(
            user_id=request.user_id,
            session_id=session_id,
            content=request.message,
            role=MessageRole.USER,
        )
        self._append_message(session_id, user_message)

        try:
            result = await self._supervisor.execute(
                user_id=request.user_id,
                situation=request.message,
            )
        except ValueError as exc:
            raise exc
        except SupervisorException as exc:
            raise RuntimeError(str(exc)) from exc

        # Persist recommended products to demo cart
        cart_products = result.cart.get("products", [])
        if cart_products:
            CartService.set_demo_cart(str(request.user_id), cart_products)
            logger.info(
                "Chat-to-cart: %d products added to demo cart for user %s",
                len(cart_products),
                request.user_id,
            )

        assistant_message = AgentMessage(
            user_id=request.user_id,
            session_id=session_id,
            content=self._sanitize_response(result.conversation_reply, result.reasoning, cart_products),
            role=MessageRole.ASSISTANT,
            metadata={
                "has_products": len(cart_products) > 0,
                "product_count": len(cart_products),
            },
        )
        self._append_message(session_id, assistant_message)

        return ChatResponse(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            cart=result.cart,
            urgency=result.urgency,
            reasoning=result.reasoning,
            eco_alternative=result.eco_alternative,
            metadata=result.metadata,
        )

    def get_history(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
    ) -> ChatHistoryResponse:
        messages = list(self._sessions.get(session_id, []))
        if messages and messages[0].user_id != user_id:
            raise PermissionError("Session does not belong to the requested user")

        return ChatHistoryResponse(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
        )

    def _append_message(
        self,
        session_id: UUID,
        message: AgentMessage,
    ) -> None:
        self._sessions.setdefault(session_id, []).append(message)

    @staticmethod
    def _sanitize_response(
        conversation_reply: str,
        reasoning: str,
        cart_products: list[dict],
    ) -> str:
        """Ensure the response shown to users is never raw JSON or technical data.

        Priority:
        1. Use conversation_reply if it's a clean natural language response
        2. Use reasoning only if it doesn't look like JSON
        3. Generate a fallback from product data
        """
        # Try conversation_reply first
        if conversation_reply and conversation_reply.strip():
            text = conversation_reply.strip()
            # Reject if it looks like JSON
            if not text.startswith("{") and not text.startswith("["):
                return text

        # Try reasoning (but reject if JSON-like)
        if reasoning and reasoning.strip():
            text = reasoning.strip()
            if not text.startswith("{") and not text.startswith("[") and "score" not in text[:50].lower():
                return text

        # Fallback: generate from product data
        if cart_products:
            top = cart_products[0]
            title = top.get("title", "a product")
            price = top.get("price", 0)
            count = len(cart_products)
            return (
                f"I found {count} products for you! "
                f"My top pick is **{title}** for ₹{price:.0f}. "
                f"Would you like me to add it to your cart?"
            )

        return "I'm looking into that for you. Could you tell me more about what you need?"
