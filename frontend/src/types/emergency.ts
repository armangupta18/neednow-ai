export interface EmergencyAnalyzeRequest {
  user_id: string;
  text: string;
  user_context?: Record<string, unknown>;
}

export interface EmergencyAnalyzeResponse {
  user_id: string;
  urgency: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score: number;
  explanation: string;
  is_emergency: boolean;
  escalation_recommended: boolean;
}

export interface EmergencyEscalateRequest {
  user_id: string;
  text: string;
  user_context?: Record<string, unknown>;
  contact_phone?: string | null;
}

export interface EmergencyEscalateResponse {
  user_id: string;
  escalated: boolean;
  urgency: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score: number;
  workflow_id: string;
  message: string;
  actions: string[];
}
