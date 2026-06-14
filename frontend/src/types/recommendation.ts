/**
 * Recommendation types — maps to backend recommendation service.
 */

import type { EcoAlternative as AgentEcoAlternative, Urgency, SupervisorCart } from "./agent";

// Re-export the correct type for new code
export type { AgentEcoAlternative as EcoAlternativeV2 };

/** Legacy EcoAlternative shape (used by existing components) */
export interface EcoAlternative {
  name: string;
  eco_score: number;
  carbon_saved: string;
}

// ---------------------------------------------------------------------------
// Recommendation Request / Response (from dedicated API)
// ---------------------------------------------------------------------------

export interface RecommendationRequest {
  user_id: string;
  session_id: string;
  query: string;
}

export interface RecommendationItem {
  product_id: string;
  title: string;
  category: string;
  price: number;
  similarity_score: number;
  ranking_score: number;
  in_stock: boolean;
}

export interface RecommendationResponse {
  user_id: string;
  recommended_products: RecommendationItem[];
  bundle_products: RecommendationItem[];
  eco_alternatives: EcoAlternative[];
  personalization_applied: boolean;
  confidence: number;
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

// ---------------------------------------------------------------------------
// Recommendation History
// ---------------------------------------------------------------------------

export interface RecommendationRecord {
  id: string;
  user_id: string;
  session_id: string;
  product_id: string;
  product_name: string;
  score: number;
  reason: string;
  agent_source: string;
  created_at: string;
}

export interface RecommendationListResponse {
  success: boolean;
  count: number;
  recommendations: RecommendationRecord[];
}

// ---------------------------------------------------------------------------
// Sustainability Recommendations
// ---------------------------------------------------------------------------

export interface SustainabilityRecommendRequest {
  product_ids: string[];
}

export interface SustainabilityRecommendResponse {
  recommendations: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

// ---------------------------------------------------------------------------
// Full Pipeline Result (what the UI consumes after chat)
// ---------------------------------------------------------------------------

export interface PipelineResult {
  /** Session for continuity */
  sessionId: string;
  /** Assistant's text reply */
  assistantReply: string;
  /** Recommended products */
  cart: SupervisorCart;
  /** Urgency assessment */
  urgency: Urgency;
  /** AI reasoning */
  reasoning: string;
  /** Eco-friendly alternative */
  ecoAlternative: EcoAlternative | null;
  /** Confidence score */
  confidence: number;
  /** Whether user memory was used */
  personalized: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Convert ChatResponse to UI-friendly PipelineResult */
export function toPipelineResult(chat: {
  session_id: string;
  assistant_message: { content: string };
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  metadata: { confidence: number; memory_used: boolean };
}): PipelineResult {
  return {
    sessionId: chat.session_id,
    assistantReply: chat.assistant_message.content,
    cart: chat.cart,
    urgency: chat.urgency,
    reasoning: chat.reasoning,
    ecoAlternative: chat.eco_alternative,
    confidence: chat.metadata.confidence,
    personalized: chat.metadata.memory_used,
  };
}


// ---------------------------------------------------------------------------
// Backward Compatibility (legacy component imports)
// ---------------------------------------------------------------------------

/** @deprecated Use RecommendedProduct instead */
export interface Product {
  id: string;
  name: string;
  price: number;
  quantity: number;
  image_url?: string;
  reason?: string;
}

/** @deprecated Use ChatResponse from ./agent instead */
export interface SupervisorResponse {
  intent: string;
  urgency_level: string;
  reasoning: string;
  products: Product[];
  eco_alternative?: {
    name: string;
    eco_score: number;
    carbon_saved: string;
  };
}
