import api from "./api";
import { ENDPOINTS } from "@/constants/api";
import type { VoiceTranscribeResponse, VoiceChatResponse } from "@/types/voice";

export async function transcribeAudio(file: File, userId: string, language = "en") {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<VoiceTranscribeResponse>(
    ENDPOINTS.VOICE.TRANSCRIBE,
    formData,
    {
      params: { user_id: userId, language },
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

export async function voiceChat(file: File, userId: string, sessionId?: string) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<VoiceChatResponse>(
    ENDPOINTS.VOICE.CHAT,
    formData,
    {
      params: { user_id: userId, session_id: sessionId, language: "en" },
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}
