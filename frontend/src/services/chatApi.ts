import api from "./api";
import { ENDPOINTS } from "@/constants/api";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export async function sendChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>(ENDPOINTS.CHAT, request, { signal });
  return response.data;
}

export async function getChatHistory(sessionId: string, userId: string) {
  const response = await api.get(ENDPOINTS.CHAT_HISTORY(sessionId), {
    params: { user_id: userId },
  });
  return response.data;
}
