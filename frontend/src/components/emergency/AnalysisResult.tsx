"use client";

import { cn } from "@/lib/utils";
import { URGENCY_CONFIG, EMERGENCY_ACTIONS } from "@/constants/emergency";
import type { UrgencyLevel } from "@/constants/emergency";

interface AnalysisResultProps {
  urgency: UrgencyLevel;
  score: number;
  explanation: string;
  isEmergency: boolean;
  escalationRecommended: boolean;
  onEscalate: () => void;
  onGetProducts: () => void;
  isEscalating?: boolean;
}

export default function AnalysisResult({
  urgency,
  score,
  explanation,
  isEmergency,
  escalationRecommended,
  onEscalate,
  onGetProducts,
  isEscalating,
}: AnalysisResultProps) {
  const config = URGENCY_CONFIG[urgency];

  return (
    <div className={cn("rounded-xl border-2 p-5 space-y-4 animate-scale-in", config.borderColor, config.bgColor)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <h3 className={cn("text-lg font-bold", config.color)}>{config.label}</h3>
            <p className="text-xs text-slate-500">{config.deliveryLabel} • {config.estimatedTime}</p>
          </div>
        </div>
        <div className={cn("text-3xl font-black", config.color)}>{score}</div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-slate-700 leading-relaxed">{explanation}</p>

      {/* Score bar */}
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={cn("h-full rounded-full transition-all duration-700", {
            "bg-green-500": urgency === "LOW",
            "bg-amber-500": urgency === "MEDIUM",
            "bg-orange-500": urgency === "HIGH",
            "bg-red-500": urgency === "CRITICAL",
          })}
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Emergency badge */}
      {isEmergency && (
        <div className="rounded-lg bg-red-600 px-4 py-2 text-center text-sm font-bold text-white shadow-md animate-pulse-glow">
          🚨 EMERGENCY DETECTED — Priority Delivery Activated
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2 pt-2">
        <button
          onClick={onGetProducts}
          className="flex-1 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-slate-800"
        >
          🛒 Get Products Now
        </button>
        {escalationRecommended && (
          <button
            onClick={onEscalate}
            disabled={isEscalating}
            className="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-red-700 disabled:opacity-50"
          >
            {isEscalating ? "Escalating..." : "⚡ Escalate Emergency"}
          </button>
        )}
      </div>
    </div>
  );
}
