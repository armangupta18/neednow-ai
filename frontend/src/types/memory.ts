/**
 * Memory types — maps to backend memory engine and user preferences.
 */

// ---------------------------------------------------------------------------
// User Memory (from GET /api/v1/memory/{user_id})
// ---------------------------------------------------------------------------

export interface UserMemory {
  dietary_preferences: string[];
  preferred_brands: string[];
  budget_level: BudgetLevel | null;
  family_size: number | null;
  purchase_patterns: string[];
  sustainability_score: number;
}

export type BudgetLevel = "low" | "medium" | "high" | "premium";

// ---------------------------------------------------------------------------
// Memory API
// ---------------------------------------------------------------------------

export interface StoreMemoryRequest {
  user_id: string;
  memory: Partial<UserMemory>;
}

export interface MemoryResponse {
  user_id: string;
  memory: UserMemory;
}

export interface ClearMemoryResponse {
  user_id: string;
  cleared: boolean;
  message: string;
}

// ---------------------------------------------------------------------------
// Short-Term Memory (session context)
// ---------------------------------------------------------------------------

export interface ShortTermMemory {
  session_context: Record<string, unknown>;
  recent_queries: string[];
  current_cart_state: Record<string, unknown>;
  last_interaction_timestamp: string;
  interaction_count: number;
  active_urgency_level: string | null;
}

// ---------------------------------------------------------------------------
// Long-Term Memory (persistent preferences)
// ---------------------------------------------------------------------------

export interface LongTermMemory {
  dietary_preferences: string[];
  preferred_brands: string[];
  budget_level: BudgetLevel | null;
  family_size: number | null;
  purchase_patterns: string[];
  sustainability_score: number;
  total_purchases: number;
  favorite_categories: string[];
  past_urgency_patterns: Record<string, number>;
  created_at: string;
  last_updated_at: string;
}

// ---------------------------------------------------------------------------
// Memory State (combined)
// ---------------------------------------------------------------------------

export interface MemoryState {
  user_id: string;
  short_term: ShortTermMemory;
  long_term: LongTermMemory;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Default empty memory for new users */
export const DEFAULT_MEMORY: UserMemory = {
  dietary_preferences: [],
  preferred_brands: [],
  budget_level: null,
  family_size: null,
  purchase_patterns: [],
  sustainability_score: 0,
};

/** Budget level display labels */
export const BUDGET_LABELS: Record<BudgetLevel, string> = {
  low: "Budget-Friendly",
  medium: "Moderate",
  high: "Premium",
  premium: "Luxury",
};
