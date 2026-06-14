/**
 * Agent pipeline configuration constants.
 *
 * Defines agent names, capabilities, display metadata, and
 * configuration for the multi-agent supervisor system.
 */

// ---------------------------------------------------------------------------
// Agent Identifiers
// ---------------------------------------------------------------------------

export const AGENTS = {
  SUPERVISOR: "supervisor",
  INTENT: "intent",
  URGENCY: "urgency",
  PRODUCT: "product",
  SUSTAINABILITY: "sustainability",
  MEMORY: "memory",
  EMERGENCY: "emergency",
} as const;

export type AgentId = (typeof AGENTS)[keyof typeof AGENTS];

// ---------------------------------------------------------------------------
// Agent Display Metadata
// ---------------------------------------------------------------------------

export interface AgentInfo {
  id: AgentId;
  name: string;
  description: string;
  icon: string;
  color: string;
}

export const AGENT_INFO: Record<AgentId, AgentInfo> = {
  supervisor: {
    id: "supervisor",
    name: "Supervisor",
    description: "Orchestrates all agents and builds the final response",
    icon: "🎯",
    color: "text-purple-600",
  },
  intent: {
    id: "intent",
    name: "Intent Agent",
    description: "Detects shopping category, urgency, and budget from your situation",
    icon: "🧠",
    color: "text-blue-600",
  },
  urgency: {
    id: "urgency",
    name: "Urgency Agent",
    description: "Scores urgency level and identifies emergency situations",
    icon: "⚡",
    color: "text-orange-600",
  },
  product: {
    id: "product",
    name: "Product Agent",
    description: "Finds and ranks products using semantic search across 60K+ items",
    icon: "🛒",
    color: "text-green-600",
  },
  sustainability: {
    id: "sustainability",
    name: "Sustainability Agent",
    description: "Evaluates eco-friendliness and suggests greener alternatives",
    icon: "🌱",
    color: "text-emerald-600",
  },
  memory: {
    id: "memory",
    name: "Memory Engine",
    description: "Learns and applies your preferences, purchase history, and patterns",
    icon: "🧬",
    color: "text-indigo-600",
  },
  emergency: {
    id: "emergency",
    name: "Emergency Agent",
    description: "Handles critical situations with priority delivery and escalation",
    icon: "🚨",
    color: "text-red-600",
  },
};

// ---------------------------------------------------------------------------
// Pipeline Configuration
// ---------------------------------------------------------------------------

/** Pipeline step display order */
export const PIPELINE_STEPS = [
  { agent: AGENTS.INTENT, label: "Understanding your situation" },
  { agent: AGENTS.URGENCY, label: "Assessing urgency" },
  { agent: AGENTS.PRODUCT, label: "Finding products" },
  { agent: AGENTS.SUSTAINABILITY, label: "Checking sustainability" },
] as const;

/** Model information */
export const MODEL_CONFIG = {
  LLM: {
    provider: "Google Gemini",
    model: "Gemini 2.5 Flash",
    modelId: "gemini-2.5-flash",
    maxTokens: 4096,
  },
  EMBEDDING: {
    provider: "Sentence Transformers",
    model: "all-MiniLM-L6-v2",
    dimensions: 384,
  },
  VECTOR_STORE: {
    provider: "ChromaDB",
    totalProducts: 60288,
    metric: "cosine",
  },
} as const;

// ---------------------------------------------------------------------------
// Confidence Thresholds
// ---------------------------------------------------------------------------

export const CONFIDENCE = {
  HIGH: 0.8,
  MEDIUM: 0.5,
  LOW: 0.3,
} as const;

export function getConfidenceLabel(score: number): string {
  if (score >= CONFIDENCE.HIGH) return "High Confidence";
  if (score >= CONFIDENCE.MEDIUM) return "Moderate Confidence";
  return "Low Confidence";
}

export function getConfidenceColor(score: number): string {
  if (score >= CONFIDENCE.HIGH) return "text-green-600";
  if (score >= CONFIDENCE.MEDIUM) return "text-amber-600";
  return "text-red-500";
}

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------

export const PRODUCT_CATEGORIES = [
  "Groceries",
  "Medicine",
  "Baby Care",
  "Personal Care",
  "Electronics",
  "Home Essentials",
  "Vitamins",
  "First Aid",
  "Hygiene",
  "Elderly Care",
  "Pet Care",
  "Party",
  "Travel",
  "Cleaning",
] as const;

export type ProductCategory = (typeof PRODUCT_CATEGORIES)[number];
