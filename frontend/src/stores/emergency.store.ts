/**
 * Emergency Store — manages emergency mode state.
 */

import { create } from "zustand";
import type { UrgencyLevel } from "@/constants/emergency";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EmergencyAnalysis {
  urgency: UrgencyLevel;
  score: number;
  explanation: string;
  isEmergency: boolean;
  escalationRecommended: boolean;
}

interface EscalationResult {
  escalated: boolean;
  workflowId: string;
  message: string;
  actions: string[];
}

interface EmergencyState {
  // State
  isActive: boolean;
  analysis: EmergencyAnalysis | null;
  escalation: EscalationResult | null;
  isAnalyzing: boolean;
  isEscalating: boolean;
  error: string | null;

  // Actions
  activateEmergency: () => void;
  deactivateEmergency: () => void;
  setAnalysis: (analysis: EmergencyAnalysis) => void;
  setEscalation: (escalation: EscalationResult) => void;
  setAnalyzing: (analyzing: boolean) => void;
  setEscalating: (escalating: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

// ---------------------------------------------------------------------------
// Store (no persistence — emergency state is session-only)
// ---------------------------------------------------------------------------

export const useEmergencyStore = create<EmergencyState>((set) => ({
  // Initial state
  isActive: false,
  analysis: null,
  escalation: null,
  isAnalyzing: false,
  isEscalating: false,
  error: null,

  // Actions
  activateEmergency: () => set({ isActive: true, error: null }),

  deactivateEmergency: () =>
    set({ isActive: false, analysis: null, escalation: null, error: null }),

  setAnalysis: (analysis) =>
    set({ analysis, isAnalyzing: false }),

  setEscalation: (escalation) =>
    set({ escalation, isEscalating: false }),

  setAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),

  setEscalating: (escalating) => set({ isEscalating: escalating }),

  setError: (error) =>
    set({ error, isAnalyzing: false, isEscalating: false }),

  reset: () =>
    set({
      isActive: false,
      analysis: null,
      escalation: null,
      isAnalyzing: false,
      isEscalating: false,
      error: null,
    }),
}));

// ---------------------------------------------------------------------------
// Selectors
// ---------------------------------------------------------------------------

export const selectIsEmergencyActive = (state: EmergencyState) => state.isActive;
export const selectEmergencyAnalysis = (state: EmergencyState) => state.analysis;
export const selectEscalation = (state: EmergencyState) => state.escalation;
export const selectIsAnalyzing = (state: EmergencyState) => state.isAnalyzing;
export const selectIsEscalating = (state: EmergencyState) => state.isEscalating;
export const selectEmergencyError = (state: EmergencyState) => state.error;
export const selectIsEmergencyLevel = (state: EmergencyState) =>
  state.analysis?.isEmergency ?? false;
export const selectUrgencyLevel = (state: EmergencyState) =>
  state.analysis?.urgency ?? null;
