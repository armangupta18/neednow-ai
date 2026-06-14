export interface AgentMessage {
  user_id: string;
  session_id: string;
  content: string;
  role: "user" | "assistant" | "system";
  metadata: Record<string, unknown>;
  timestamp: string;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  session_id?: string | null;
}

export interface CartProduct {
  id: string;
  title: string;
  price: number;
  score: number;
}

export interface BundleProduct {
  id: string;
  title: string;
  price: number;
}

export interface SupervisorCart {
  category: string;
  products: CartProduct[];
  bundles: BundleProduct[];
}

export interface Urgency {
  level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score: number;
  explanation: string;
}

export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

export interface ChatResponse {
  session_id: string;
  user_message: AgentMessage;
  assistant_message: AgentMessage;
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  recommended_products: Record<string, unknown>[];
  metadata: { memory_used: boolean; confidence: number };
  timestamp: string;
}
