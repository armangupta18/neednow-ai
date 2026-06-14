"use client";

import { useRouter } from "next/navigation";
import { useEmergency } from "@/hooks/useEmergency";
import { useChat } from "@/hooks/useChat";
import {
  EmergencyInput,
  QuickActions,
  AnalysisResult,
  EscalationResult,
} from "@/components/emergency";
import { EMERGENCY_DISCLAIMER } from "@/constants/emergency";
import { ROUTES } from "@/constants/routes";

export default function EmergencyPage() {
  const router = useRouter();
  const {
    analysis,
    escalation,
    isAnalyzing,
    isEscalating,
    error,
    analyze,
    escalate,
  } = useEmergency();
  const { sendMessage } = useChat();

  const handleAnalyze = async (text: string) => {
    await analyze(text);
  };

  const handleEscalate = async () => {
    if (!analysis) return;
    await escalate(analysis.explanation);
  };

  const handleGetProducts = async () => {
    if (!analysis) return;
    await sendMessage(analysis.explanation);
    router.push(ROUTES.CHAT);
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 animate-pulse-glow">
          <span className="text-3xl">🚨</span>
        </div>
        <h1 className="text-3xl font-extrabold text-red-700">Emergency Mode</h1>
        <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
          Priority delivery for urgent medical, baby care, and safety needs.
          Describe your situation for instant analysis.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="mb-6 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
        <p className="text-xs text-amber-700 leading-relaxed">{EMERGENCY_DISCLAIMER}</p>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Escalation result (top, if present) */}
        {escalation && (
          <EscalationResult
            escalated={escalation.escalated}
            workflowId={escalation.workflowId}
            message={escalation.message}
            actions={escalation.actions}
          />
        )}

        {/* Analysis result */}
        {analysis && !escalation && (
          <AnalysisResult
            urgency={analysis.urgency}
            score={analysis.score}
            explanation={analysis.explanation}
            isEmergency={analysis.isEmergency}
            escalationRecommended={analysis.escalationRecommended}
            onEscalate={handleEscalate}
            onGetProducts={handleGetProducts}
            isEscalating={isEscalating}
          />
        )}

        {/* Input */}
        <EmergencyInput onSubmit={handleAnalyze} loading={isAnalyzing} />

        {/* Quick actions */}
        <QuickActions onSelect={handleAnalyze} disabled={isAnalyzing} />
      </div>
    </div>
  );
}
