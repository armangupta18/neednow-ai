/**
 * Agent Service — connects to the supervisor/chat pipeline and emergency APIs.
 */

import { apiPost, apiGet } from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";
import type {
  ChatRequest,
  ChatResponse,
  IntentResponse,
  EmergencyAnalyzeRequest,
  EmergencyAnalyzeResponse,
  EmergencyEscalateRequest,
  EmergencyEscalateResponse,
} from "@/types/agent";

// ---------------------------------------------------------------------------
// Chat / Supervisor Pipeline
// ---------------------------------------------------------------------------

/** Send a chat message through the full agent pipeline */
export async function sendMessage(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  return apiPost<ChatResponse>(API_ROUTES.CHAT, request, { signal });
}

/** Get chat history for a session */
export async function getChatHistory(
  sessionId: string,
  userId: string
): Promise<{ session_id: string; user_id: string; messages: unknown[] }> {
  return apiGet(API_ROUTES.CHAT_HISTORY(sessionId), {
    params: { user_id: userId },
  });
}

// ---------------------------------------------------------------------------
// Intent Analysis
// ---------------------------------------------------------------------------

/** Analyze intent from text (standalone, without full pipeline) */
export async function analyzeIntent(
  text: string,
  userId: string
): Promise<IntentResponse> {
  return apiPost<IntentResponse>(API_ROUTES.INTENT, {
    text,
    user_id: userId,
  });
}

// ---------------------------------------------------------------------------
// Emergency
// ---------------------------------------------------------------------------

/** Analyze urgency and emergency level */
export async function analyzeEmergency(
  request: EmergencyAnalyzeRequest
): Promise<EmergencyAnalyzeResponse> {
  return apiPost<EmergencyAnalyzeResponse>(
    API_ROUTES.EMERGENCY.ANALYZE,
    request
  );
}

/** Escalate an emergency — trigger priority workflow */
export async function escalateEmergency(
  request: EmergencyEscalateRequest
): Promise<EmergencyEscalateResponse> {
  return apiPost<EmergencyEscalateResponse>(
    API_ROUTES.EMERGENCY.ESCALATE,
    request
  );
}

/** Check emergency subsystem health */
export async function checkEmergencyHealth(): Promise<{
  status: string;
  urgency_agent: string;
  emergency_agent: string;
}> {
  return apiGet(API_ROUTES.EMERGENCY.HEALTH);
}
