/**
 * Voice Service — connects to voice transcription and voice chat APIs.
 */

import api from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TranscribeResponse {
  user_id: string;
  text: string;
  confidence: number;
  language: string;
  duration_seconds: number;
}

export interface VoiceChatResponse {
  session_id: string;
  user_id: string;
  transcribed_text: string;
  confidence: number;
  assistant_reply: string;
  cart: Record<string, unknown>;
  urgency: Record<string, unknown> | null;
  eco_alternative: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/** Transcribe an audio file to text */
export async function transcribeAudio(
  file: File,
  userId: string,
  language = "en"
): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<TranscribeResponse>(
    API_ROUTES.VOICE.TRANSCRIBE,
    formData,
    {
      params: { user_id: userId, language },
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000, // Voice files may take longer
    }
  );
  return response.data;
}

/** Send audio through the full voice→chat pipeline */
export async function voiceChat(
  file: File,
  userId: string,
  options?: { sessionId?: string; language?: string }
): Promise<VoiceChatResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<VoiceChatResponse>(
    API_ROUTES.VOICE.CHAT,
    formData,
    {
      params: {
        user_id: userId,
        session_id: options?.sessionId,
        language: options?.language ?? "en",
      },
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    }
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Audio Helpers
// ---------------------------------------------------------------------------

/** Supported audio MIME types */
export const SUPPORTED_AUDIO_TYPES = [
  "audio/wav",
  "audio/webm",
  "audio/mp3",
  "audio/mpeg",
  "audio/mp4",
  "audio/m4a",
  "audio/ogg",
] as const;

/** Max audio file size (25MB) */
export const MAX_AUDIO_SIZE = 25 * 1024 * 1024;

/** Validate an audio file before upload */
export function validateAudioFile(file: File): string | null {
  if (!SUPPORTED_AUDIO_TYPES.includes(file.type as typeof SUPPORTED_AUDIO_TYPES[number])) {
    return `Unsupported format: ${file.type}. Use WAV, WebM, MP3, or M4A.`;
  }
  if (file.size > MAX_AUDIO_SIZE) {
    return `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max: 25MB.`;
  }
  return null;
}
