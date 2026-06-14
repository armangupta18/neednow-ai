/**
 * UI prompts, placeholders, and messaging constants.
 *
 * Centralized text for consistent UX copy across the application.
 */

// ---------------------------------------------------------------------------
// Chat Interface
// ---------------------------------------------------------------------------

export const CHAT_PLACEHOLDERS = [
  "Describe your situation... (e.g., 'My baby has a fever')",
  "What do you need right now? (e.g., 'Guests arriving in 30 minutes')",
  "Tell me what's happening... (e.g., 'Running out of insulin')",
  "How can I help? (e.g., 'Need first aid kit urgently')",
] as const;

export const CHAT_WELCOME_MESSAGE =
  "Hi! I'm NeedNow AI. Tell me your situation and I'll find exactly what you need — fast.";

export const CHAT_THINKING_MESSAGE = "Analyzing your situation...";

export const CHAT_ERROR_MESSAGE =
  "I'm having trouble processing that. Please try again or rephrase your request.";

// ---------------------------------------------------------------------------
// Situation Input (Home Page)
// ---------------------------------------------------------------------------

export const SITUATION_PLACEHOLDER =
  "Describe your situation in detail... (e.g., 'My infant needs formula, she hasn't eaten in 4 hours and I'm home alone')";

export const SITUATION_EXAMPLES = [
  "My baby has a high fever and needs medicine immediately",
  "8 friends coming over in 20 minutes, need party snacks",
  "Running low on insulin, need it delivered today",
  "Father is bedridden and needs adult diapers urgently",
  "Looking for eco-friendly cleaning products for the house",
  "Need a first aid kit — my child got a minor cut",
] as const;

// ---------------------------------------------------------------------------
// Voice Commerce
// ---------------------------------------------------------------------------

export const VOICE_START_PROMPT = "Press and hold to speak your situation";
export const VOICE_RECORDING_PROMPT = "Listening... Release to send";
export const VOICE_PROCESSING_PROMPT = "Transcribing your message...";

// ---------------------------------------------------------------------------
// Emergency Mode
// ---------------------------------------------------------------------------

export const EMERGENCY_PROMPT =
  "Describe your emergency. We'll prioritize immediate delivery and escalate if needed.";

export const EMERGENCY_ESCALATION_MESSAGE =
  "Your request has been escalated for priority processing. An agent will assist you.";

// ---------------------------------------------------------------------------
// Empty States
// ---------------------------------------------------------------------------

export const EMPTY_STATES = {
  CART: {
    title: "Your cart is empty",
    description: "Start a conversation and we'll recommend products for you.",
  },
  HISTORY: {
    title: "No conversations yet",
    description: "Start chatting to see your history here.",
  },
  RECOMMENDATIONS: {
    title: "No recommendations yet",
    description: "Tell us your situation to get personalized suggestions.",
  },
  MEMORY: {
    title: "No preferences saved",
    description: "We'll learn your preferences as you shop.",
  },
  SEARCH: {
    title: "No results found",
    description: "Try a different search or rephrase your query.",
  },
} as const;

// ---------------------------------------------------------------------------
// Success Messages
// ---------------------------------------------------------------------------

export const SUCCESS_MESSAGES = {
  CART_ADDED: "Added to cart",
  CART_REMOVED: "Removed from cart",
  CART_CLEARED: "Cart cleared",
  MEMORY_SAVED: "Preferences saved",
  MEMORY_CLEARED: "Preferences reset",
} as const;
