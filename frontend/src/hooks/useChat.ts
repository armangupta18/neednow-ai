"use client";

import { useCallback, useRef } from "react";
import { sendMessage, getChatHistory } from "@/services/agent.service";
import { useChatStore } from "@/stores/chat.store";
import { useUserStore } from "@/stores/user.store";
import type { ChatResponse } from "@/types/agent";
import { generateId } from "@/lib/utils";

/**
 * Chat hook — sends messages through the agent pipeline.
 * Manages loading, errors, abort, and store updates.
 */
export function useChat() {
  const abortRef = useRef<AbortController | null>(null);

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

  const error = useChatStore((s) => {
    // Derive from last message metadata
    return null;
  });

  const sendChatMessage = useCallback(
    async (message: string): Promise<ChatResponse | null> => {
      if (!message.trim()) return null;
      console.log("[useChat] sendChatMessage called:", message);

      // Abort any in-flight request
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      // Optimistic: add user message immediately
      const userMsgId = generateId();
      addMessage({
        id: userMsgId,
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

        console.log("[useChat] Response received:", response.session_id);

        // Update store
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
        console.error("[useChat] Error:", msg);

        addMessage({
          id: generateId(),
          role: "assistant",
          content: `⚠️ ${msg}. Please check that the backend is running at ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}.`,
          timestamp: new Date().toISOString(),
          metadata: { error: true },
        });
        return null;
      } finally {
        setIsTyping(false);
      }
    },
    [userId, sessionId, addMessage, setSessionId, setLastResult, setIsTyping]
  );

  const loadHistory = useCallback(
    async (sid: string) => {
      try {
        const data = await getChatHistory(sid, userId);
        return data;
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
    // State
    messages,
    lastResult,
    isTyping,
    sessionId,
    error,
    // Actions
    sendMessage: sendChatMessage,
    loadHistory,
    cancel,
    clearChat,
    newSession,
  };
}
