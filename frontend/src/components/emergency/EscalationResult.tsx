"use client";

import { EMERGENCY_ACTIONS } from "@/constants/emergency";

interface EscalationResultProps {
  escalated: boolean;
  workflowId: string;
  message: string;
  actions: string[];
}

export default function EscalationResult({
  escalated,
  workflowId,
  message,
  actions,
}: EscalationResultProps) {
  if (!escalated) return null;

  return (
    <div className="rounded-xl border-2 border-green-300 bg-green-50 p-5 space-y-4 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500 text-white text-lg">
          ✓
        </span>
        <div>
          <h3 className="text-lg font-bold text-green-800">Emergency Escalated</h3>
          <p className="text-xs text-green-600">Workflow ID: {workflowId}</p>
        </div>
      </div>

      {/* Message */}
      <p className="text-sm text-green-800 leading-relaxed font-medium">{message}</p>

      {/* Actions taken */}
      {actions.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-green-700 mb-2">
            Actions Triggered
          </h4>
          <div className="flex flex-wrap gap-2">
            {actions.map((action) => {
              const actionConfig = Object.values(EMERGENCY_ACTIONS).find(
                (a) => a.id === action
              );
              return (
                <span
                  key={action}
                  className="inline-flex items-center gap-1.5 rounded-full bg-green-100 border border-green-200 px-3 py-1 text-xs font-medium text-green-800"
                >
                  <span>{actionConfig?.icon ?? "✓"}</span>
                  {actionConfig?.label ?? action}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
