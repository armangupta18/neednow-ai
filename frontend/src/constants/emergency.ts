/**
 * Emergency mode configuration constants.
 *
 * Defines urgency levels, emergency actions, delivery priorities,
 * and UI configuration for emergency situations.
 */

// ---------------------------------------------------------------------------
// Urgency Levels
// ---------------------------------------------------------------------------

export const URGENCY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
export type UrgencyLevel = (typeof URGENCY_LEVELS)[number];

export const URGENCY_CONFIG: Record<
  UrgencyLevel,
  {
    label: string;
    description: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: string;
    deliveryLabel: string;
    estimatedTime: string;
  }
> = {
  LOW: {
    label: "Low Priority",
    description: "Standard delivery timeline",
    color: "text-green-700",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    icon: "✅",
    deliveryLabel: "Standard Delivery",
    estimatedTime: "2-3 days",
  },
  MEDIUM: {
    label: "Medium Priority",
    description: "Needed today, not immediately",
    color: "text-amber-700",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    icon: "⚠️",
    deliveryLabel: "Same-Day Delivery",
    estimatedTime: "4-8 hours",
  },
  HIGH: {
    label: "High Priority",
    description: "Urgent need within hours",
    color: "text-orange-700",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    icon: "🔴",
    deliveryLabel: "Express Delivery",
    estimatedTime: "1-2 hours",
  },
  CRITICAL: {
    label: "Emergency",
    description: "Life-threatening or immediate medical need",
    color: "text-red-700",
    bgColor: "bg-red-50",
    borderColor: "border-red-300",
    icon: "🚨",
    deliveryLabel: "Emergency Delivery",
    estimatedTime: "30 minutes",
  },
};

// ---------------------------------------------------------------------------
// Emergency Actions
// ---------------------------------------------------------------------------

export const EMERGENCY_ACTIONS = {
  PRIORITY_DELIVERY: {
    id: "priority_delivery",
    label: "Priority Delivery",
    description: "Expedite to fastest available courier",
    icon: "🚀",
  },
  NOTIFY_SUPPORT: {
    id: "notify_support",
    label: "Notify Support",
    description: "Alert customer support team",
    icon: "📞",
  },
  WAIVE_FEES: {
    id: "waive_fees",
    label: "Waive Delivery Fees",
    description: "Remove delivery charges for emergency",
    icon: "💸",
  },
  CONTACT_PHARMACY: {
    id: "contact_pharmacy",
    label: "Contact Pharmacy",
    description: "Coordinate with nearest pharmacy",
    icon: "💊",
  },
  ALTERNATIVE_SOURCE: {
    id: "alternative_source",
    label: "Alternative Source",
    description: "Find item from nearby store if out of stock",
    icon: "🏪",
  },
} as const;

export type EmergencyActionId = keyof typeof EMERGENCY_ACTIONS;

// ---------------------------------------------------------------------------
// Emergency Keywords (trigger detection)
// ---------------------------------------------------------------------------

export const EMERGENCY_KEYWORDS = [
  "emergency",
  "urgent",
  "immediately",
  "critical",
  "life-threatening",
  "choking",
  "allergic reaction",
  "asthma attack",
  "insulin",
  "bleeding",
  "fever",
  "can't breathe",
  "diabetic",
  "seizure",
  "overdose",
  "poisoning",
] as const;

// ---------------------------------------------------------------------------
// Emergency Contact
// ---------------------------------------------------------------------------

export const EMERGENCY_CONTACTS = {
  INDIA_EMERGENCY: "112",
  INDIA_AMBULANCE: "108",
  INDIA_POISON: "1066",
  SUICIDE_HELPLINE: "988",
} as const;

export const EMERGENCY_DISCLAIMER =
  "⚠️ For life-threatening emergencies, call 112 immediately. " +
  "NeedNow AI provides product delivery assistance, not medical advice or emergency services.";

// ---------------------------------------------------------------------------
// Score Thresholds
// ---------------------------------------------------------------------------

export const URGENCY_THRESHOLDS = {
  CRITICAL_MIN: 90,
  HIGH_MIN: 70,
  MEDIUM_MIN: 40,
  LOW_MIN: 0,
} as const;

/** Determine urgency level from a score (0-100) */
export function getUrgencyFromScore(score: number): UrgencyLevel {
  if (score >= URGENCY_THRESHOLDS.CRITICAL_MIN) return "CRITICAL";
  if (score >= URGENCY_THRESHOLDS.HIGH_MIN) return "HIGH";
  if (score >= URGENCY_THRESHOLDS.MEDIUM_MIN) return "MEDIUM";
  return "LOW";
}

/** Check if a score qualifies as an emergency */
export function isEmergencyScore(score: number): boolean {
  return score >= URGENCY_THRESHOLDS.HIGH_MIN;
}

/** Check if text contains emergency keywords */
export function containsEmergencyKeyword(text: string): boolean {
  const lower = text.toLowerCase();
  return EMERGENCY_KEYWORDS.some((keyword) => lower.includes(keyword));
}
