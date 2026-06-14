import { create } from "zustand";
import type { ChatResponse, AgentMessage } from "@/types/chat";

interface ChatState {
  sessionId: string | null;
  messages: AgentMessage[];
  lastResponse: ChatResponse | null;
  setSessionId: (id: string) => void;
  addMessage: (msg: AgentMessage) => void;
  setLastResponse: (res: ChatResponse) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  lastResponse: null,
  setSessionId: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLastResponse: (res) => set({ lastResponse: res }),
  clearChat: () => set({ sessionId: null, messages: [], lastResponse: null }),
}));
