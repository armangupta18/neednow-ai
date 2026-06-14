import api from "./api";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export async function sendChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/chat", request, { signal });
  return response.data;
}

export async function getChatHistory(sessionId: string, userId: string) {
  const response = await api.get(`/chat/${sessionId}/history`, {
    params: { user_id: userId },
  });
  return response.data;
}
