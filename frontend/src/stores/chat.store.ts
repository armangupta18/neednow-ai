/**
 * Chat Store — manages conversation state with persistence.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AgentMessage, SupervisorCart, Urgency, EcoAlternative } from "@/types/agent";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

interface LastResult {
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  ecoAlternative: EcoAlternative | null;
  confidence: number;
}

interface ChatState {
  // State
  sessionId: string | null;
  messages: ChatMessage[];
  lastResult: LastResult | null;
  isTyping: boolean;

  // Actions
  setSessionId: (id: string) => void;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  setLastResult: (result: LastResult) => void;
  setIsTyping: (typing: boolean) => void;
  clearChat: () => void;
  newSession: () => void;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      // Initial state
      sessionId: null,
      messages: [],
      lastResult: null,
      isTyping: false,

      // Actions
      setSessionId: (id) => set({ sessionId: id }),

      addMessage: (msg) =>
        set((state) => ({ messages: [...state.messages, msg] })),

      setMessages: (msgs) => set({ messages: msgs }),

      setLastResult: (result) => set({ lastResult: result }),

      setIsTyping: (typing) => set({ isTyping: typing }),

      clearChat: () =>
        set({ sessionId: null, messages: [], lastResult: null, isTyping: false }),

      newSession: () =>
        set({ sessionId: null, messages: [], lastResult: null }),
    }),
    {
      name: "neednow-chat",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
      partialize: (state) => ({
        sessionId: state.sessionId,
        messages: state.messages.slice(-50),
        lastResult: state.lastResult,
        // IMPORTANT: Do NOT persist isTyping — it must always start as false
      }),
      onRehydrateStorage: () => (state) => {
        // Ensure isTyping is always false after rehydration
        if (state) {
          state.isTyping = false;
        }
      },
    }
  )
);

// ---------------------------------------------------------------------------
// Selectors
// ---------------------------------------------------------------------------

export const selectMessages = (state: ChatState) => state.messages;
export const selectSessionId = (state: ChatState) => state.sessionId;
export const selectLastResult = (state: ChatState) => state.lastResult;
export const selectIsTyping = (state: ChatState) => state.isTyping;
export const selectMessageCount = (state: ChatState) => state.messages.length;
export const selectLastMessage = (state: ChatState) =>
  state.messages[state.messages.length - 1] ?? null;
export const selectHasSession = (state: ChatState) => state.sessionId !== null;
