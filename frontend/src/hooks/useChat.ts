"use client";

import { useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { sendMessage, getChatHistory } from "@/services/agent.service";
import { useChatStore } from "@/stores/chat.store";
import { useUserStore } from "@/stores/user.store";
import { useCartStore } from "@/stores/cart.store";
import type { ChatResponse } from "@/types/agent";
import { generateId } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

// ---------------------------------------------------------------------------
// Action Command Detection
// ---------------------------------------------------------------------------

type ActionType =
  | "add_top"
  | "add_first"
  | "add_all"
  | "view_cart"
  | "checkout"
  | "buy_now"
  | "confirm"
  | "cancel"
  | null;

const ACTION_PATTERNS: [RegExp, ActionType][] = [
  // Add to cart commands
  [/^(yes|yeah|yep|sure|ok|okay|add it|add that|add this)/i, "add_top"],
  [/^add (it|the top|top pick|first|first one|recommended)/i, "add_top"],
  [/^add (all|everything|all of them|all items)/i, "add_all"],
  [/^add (second|2nd|third|3rd|fourth|4th)/i, "add_first"], // fallback to first for now
  [/^(buy it|buy now|buy this|purchase)/i, "buy_now"],

  // Cart and checkout
  [/^(show|view|open|go to) (my )?cart/i, "view_cart"],
  [/^(checkout|check out|proceed|place order|pay)/i, "checkout"],

  // Confirmations
  [/^(confirm|yes.*order|place.*order)/i, "confirm"],
  [/^(cancel|no|never ?mind|forget it)/i, "cancel"],
];

function detectAction(message: string): ActionType {
  const trimmed = message.trim().toLowerCase();
  for (const [pattern, action] of ACTION_PATTERNS) {
    if (pattern.test(trimmed)) {
      return action;
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Chat hook — sends messages through the agent pipeline.
 * Intercepts conversational commands (add, buy, checkout) locally
 * without triggering new product searches.
 */
export function useChat() {
  const abortRef = useRef<AbortController | null>(null);
  const routerRef = useRef<ReturnType<typeof useRouter> | null>(null);

  const userId = useUserStore((s) => s.userId);
  const sessionId = useChatStore((s) => s.sessionId);
  const isTyping = useChatStore((s) => s.isTyping);
  const messages = useChatStore((s) => s.messages);
  const lastResult = useChatStore((s) => s.lastResult);

  const {
    setSessionId,
    addMessage,
    setLastResult,
    setIsTyping,
    clearChat,
    newSession,
  } = useChatStore();

  // Cart store direct access for local actions
  const cartItems = useCartStore((s) => s.items);
  const addCartItem = useCartStore((s) => s.addItem);
  const cartClearFn = useCartStore((s) => s.clearCart);

  const error = useChatStore(() => null);

  // ── Handle local action (no backend call) ──────────────────

  const handleLocalAction = useCallback(
    (action: ActionType, userMessage: string): boolean => {
      const products = lastResult?.cart?.products;
      if (!products || products.length === 0) {
        // No products in context — can't handle action locally
        if (action === "view_cart") {
          addMessage({
            id: generateId(),
            role: "user",
            content: userMessage,
            timestamp: new Date().toISOString(),
          });
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "Opening your cart now!",
            timestamp: new Date().toISOString(),
          });
          // Navigate will happen in ChatWindow
          return true;
        }
        if (action === "checkout") {
          addMessage({
            id: generateId(),
            role: "user",
            content: userMessage,
            timestamp: new Date().toISOString(),
          });
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "Taking you to checkout!",
            timestamp: new Date().toISOString(),
          });
          return true;
        }
        return false; // No context — fall through to backend
      }

      // Add user message
      addMessage({
        id: generateId(),
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString(),
      });

      switch (action) {
        case "add_top":
        case "add_first": {
          const product = products[0];
          if (!product) return false;
          addCartItem({
            id: generateId(),
            product_id: product.id,
            product_name: product.title,
            quantity: 1,
            unit_price: product.price,
            line_total: product.price,
          });
          addMessage({
            id: generateId(),
            role: "assistant",
            content: `✅ Added **${product.title}** to your cart! You can view your cart or continue shopping.`,
            timestamp: new Date().toISOString(),
            metadata: { action: "added_to_cart", productId: product.id },
          });
          return true;
        }

        case "add_all": {
          for (const product of products) {
            addCartItem({
              id: generateId(),
              product_id: product.id,
              product_name: product.title,
              quantity: 1,
              unit_price: product.price,
              line_total: product.price,
            });
          }
          addMessage({
            id: generateId(),
            role: "assistant",
            content: `✅ Added all ${products.length} products to your cart! Ready to checkout?`,
            timestamp: new Date().toISOString(),
            metadata: { action: "added_all_to_cart" },
          });
          return true;
        }

        case "buy_now": {
          const product = products[0];
          if (!product) return false;
          addCartItem({
            id: generateId(),
            product_id: product.id,
            product_name: product.title,
            quantity: 1,
            unit_price: product.price,
            line_total: product.price,
          });
          addMessage({
            id: generateId(),
            role: "assistant",
            content: `✅ **${product.title}** added! Taking you to checkout now...`,
            timestamp: new Date().toISOString(),
            metadata: { action: "buy_now", navigate: ROUTES.CHECKOUT },
          });
          return true;
        }

        case "view_cart": {
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "Opening your cart!",
            timestamp: new Date().toISOString(),
            metadata: { action: "navigate", navigate: ROUTES.CART },
          });
          return true;
        }

        case "checkout": {
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "Let's proceed to checkout!",
            timestamp: new Date().toISOString(),
            metadata: { action: "navigate", navigate: ROUTES.CHECKOUT },
          });
          return true;
        }

        case "confirm": {
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "Great! Taking you to complete your order.",
            timestamp: new Date().toISOString(),
            metadata: { action: "navigate", navigate: ROUTES.CHECKOUT },
          });
          return true;
        }

        case "cancel": {
          addMessage({
            id: generateId(),
            role: "assistant",
            content: "No problem! Let me know if you'd like to search for something else.",
            timestamp: new Date().toISOString(),
          });
          return true;
        }

        default:
          return false;
      }
    },
    [lastResult, addMessage, addCartItem]
  );

  // ── Send message (with action interception) ────────────────

  const sendChatMessage = useCallback(
    async (message: string): Promise<ChatResponse | null> => {
      if (!message.trim()) return null;

      // Check if this is a conversational action command
      const action = detectAction(message.trim());
      if (action) {
        const handled = handleLocalAction(action, message.trim());
        if (handled) {
          return null; // Handled locally — no backend call
        }
      }

      // Not an action command — send to backend for product search
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      addMessage({
        id: generateId(),
        role: "user",
        content: message.trim(),
        timestamp: new Date().toISOString(),
      });

      setIsTyping(true);

      try {
        const response = await sendMessage(
          { user_id: userId, message: message.trim(), session_id: sessionId },
          abortRef.current.signal
        );

        setSessionId(response.session_id);
        addMessage({
          id: generateId(),
          role: "assistant",
          content: response.assistant_message.content,
          timestamp: response.timestamp,
          metadata: response.metadata as unknown as Record<string, unknown>,
        });
        setLastResult({
          cart: response.cart,
          urgency: response.urgency,
          reasoning: response.reasoning,
          ecoAlternative: response.eco_alternative,
          confidence: response.metadata.confidence,
        });

        return response;
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return null;
        if (err instanceof Error && err.name === "CanceledError") return null;

        const msg = err instanceof Error ? err.message : "Failed to send message";
        addMessage({
          id: generateId(),
          role: "assistant",
          content: `⚠️ ${msg}. Please try again.`,
          timestamp: new Date().toISOString(),
          metadata: { error: true },
        });
        return null;
      } finally {
        setIsTyping(false);
      }
    },
    [userId, sessionId, addMessage, setSessionId, setLastResult, setIsTyping, handleLocalAction]
  );

  const loadHistory = useCallback(
    async (sid: string) => {
      try {
        return await getChatHistory(sid, userId);
      } catch {
        return null;
      }
    },
    [userId]
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsTyping(false);
  }, [setIsTyping]);

  return {
    messages,
    lastResult,
    isTyping,
    sessionId,
    error,
    sendMessage: sendChatMessage,
    loadHistory,
    cancel,
    clearChat,
    newSession,
  };
}
