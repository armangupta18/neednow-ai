export interface VoiceTranscribeResponse {
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
