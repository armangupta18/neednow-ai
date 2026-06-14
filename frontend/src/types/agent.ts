/**
 * Agent types — maps to backend agent pipeline responses.
 */

// ---------------------------------------------------------------------------
// Message
// ---------------------------------------------------------------------------

export type MessageRole = "user" | "assistant" | "system";

export interface AgentMessage {
  user_id: string;
  session_id: string;
  content: string;
  role: MessageRole;
  metadata: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Intent Agent
// ---------------------------------------------------------------------------

export type IntentUrgency = "low" | "medium" | "high" | "critical";

export interface IntentResponse {
  category: string;
  urgency: IntentUrgency;
  budget: number | null;
  people_count: number | null;
  confidence: number;
}

// ---------------------------------------------------------------------------
// Urgency Agent
// ---------------------------------------------------------------------------

export type UrgencyLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface UrgencyResponse {
  urgency: UrgencyLevel;
  score: number;
  explanation: string;
}

export interface Urgency {
  level: UrgencyLevel;
  score: number;
  explanation: string;
}

// ---------------------------------------------------------------------------
// Sustainability Agent
// ---------------------------------------------------------------------------

export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

export interface SustainabilityResponse {
  eco_alternatives: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

// ---------------------------------------------------------------------------
// Supervisor Agent (full pipeline response)
// ---------------------------------------------------------------------------

export interface SupervisorCart {
  category: string;
  products: Array<{
    id: string;
    title: string;
    price: number;
    score: number;
  }>;
  bundles: Array<{
    id: string;
    title: string;
    price: number;
  }>;
}

export interface SupervisorMetadata {
  memory_used: boolean;
  confidence: number;
  user_context?: string;
}

export interface SupervisorResponse {
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  metadata: SupervisorMetadata;
}

// ---------------------------------------------------------------------------
// Chat Response (from POST /api/v1/chat — wraps supervisor)
// ---------------------------------------------------------------------------

export interface ChatResponse {
  session_id: string;
  user_message: AgentMessage;
  assistant_message: AgentMessage;
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  recommended_products: Record<string, unknown>[];
  metadata: SupervisorMetadata;
  timestamp: string;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  session_id?: string | null;
}

// ---------------------------------------------------------------------------
// Emergency Agent
// ---------------------------------------------------------------------------

export interface EmergencyAnalyzeRequest {
  user_id: string;
  text: string;
  user_context?: Record<string, unknown>;
}

export interface EmergencyAnalyzeResponse {
  user_id: string;
  urgency: UrgencyLevel;
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
  urgency: UrgencyLevel;
  score: number;
  workflow_id: string;
  message: string;
  actions: string[];
}
