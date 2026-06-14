"use client";

import { useCallback } from "react";
import * as agentService from "@/services/agent.service";
import { useEmergencyStore } from "@/stores/emergency.store";
import { useUserStore } from "@/stores/user.store";
import { containsEmergencyKeyword } from "@/constants/emergency";
import type { EmergencyAnalyzeResponse, EmergencyEscalateResponse } from "@/types/agent";

/**
 * Emergency hook — manages emergency analysis, escalation, and state.
 */
export function useEmergency() {
  const userId = useUserStore((s) => s.userId);
  const {
    isActive,
    analysis,
    escalation,
    isAnalyzing,
    isEscalating,
    error,
    activateEmergency,
    deactivateEmergency,
    setAnalysis,
    setEscalation,
    setAnalyzing,
    setEscalating,
    setError,
    reset,
  } = useEmergencyStore();

  // ── Analyze ────────────────────────────────────────────────

  const analyze = useCallback(
    async (text: string): Promise<EmergencyAnalyzeResponse | null> => {
      try {
        setAnalyzing(true);
        setError(null);

        const result = await agentService.analyzeEmergency({
          user_id: userId,
          text,
        });

        setAnalysis({
          urgency: result.urgency,
          score: result.score,
          explanation: result.explanation,
          isEmergency: result.is_emergency,
          escalationRecommended: result.escalation_recommended,
        });

        // Auto-activate emergency mode if needed
        if (result.is_emergency && !isActive) {
          activateEmergency();
        }

        return result;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Analysis failed";
        setError(msg);
        return null;
      }
    },
    [userId, isActive, activateEmergency, setAnalysis, setAnalyzing, setError]
  );

  // ── Escalate ───────────────────────────────────────────────

  const escalate = useCallback(
    async (text: string, contactPhone?: string): Promise<EmergencyEscalateResponse | null> => {
      try {
        setEscalating(true);
        setError(null);

        const result = await agentService.escalateEmergency({
          user_id: userId,
          text,
          contact_phone: contactPhone ?? null,
        });

        setEscalation({
          escalated: result.escalated,
          workflowId: result.workflow_id,
          message: result.message,
          actions: result.actions,
        });

        return result;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Escalation failed";
        setError(msg);
        return null;
      }
    },
    [userId, setEscalation, setEscalating, setError]
  );

  // ── Quick Check ────────────────────────────────────────────

  /** Check text for emergency keywords (client-side, instant) */
  const quickCheck = useCallback((text: string): boolean => {
    return containsEmergencyKeyword(text);
  }, []);

  // ── Lifecycle ──────────────────────────────────────────────

  const activate = useCallback(() => {
    activateEmergency();
  }, [activateEmergency]);

  const deactivate = useCallback(() => {
    deactivateEmergency();
  }, [deactivateEmergency]);

  return {
    // State
    isActive,
    analysis,
    escalation,
    isAnalyzing,
    isEscalating,
    error,
    // Actions
    analyze,
    escalate,
    quickCheck,
    activate,
    deactivate,
    reset,
  };
}
