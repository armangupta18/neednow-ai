"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { URGENCY_CONFIG } from "@/constants/emergency";
import type { UrgencyLevel } from "@/constants/emergency";

interface ReasoningPanelProps {
  reasoning: string;
  urgency: { level: string; score: number; explanation: string };
  confidence: number;
  ecoAlternative?: {
    alternative_product_name: string;
    carbon_saved: number;
    sustainability_score: number;
  } | null;
}

export default function ReasoningPanel({
  reasoning,
  urgency,
  confidence,
  ecoAlternative,
}: ReasoningPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const level = urgency.level as UrgencyLevel;
  const config = URGENCY_CONFIG[level] ?? URGENCY_CONFIG.LOW;

  return (
    <div className="animate-fade-in-up rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">🧠</span>
          <span className="text-sm font-semibold text-slate-700">AI Reasoning</span>
          {/* Urgency badge */}
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-xs font-semibold",
              config.bgColor,
              config.color
            )}
          >
            {config.icon} {config.label}
          </span>
        </div>
        <span className="text-xs text-slate-400">
          {expanded ? "▲ Collapse" : "▼ Expand"}
        </span>
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="border-t px-4 py-4 space-y-4 animate-fade-in">
          {/* Reasoning */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
              Reasoning
            </h4>
            <p className="text-sm text-slate-700 leading-relaxed">{reasoning}</p>
          </div>

          {/* Urgency Details */}
          <div className="flex gap-4">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Urgency Score
              </h4>
              <p className={cn("text-lg font-bold", config.color)}>
                {urgency.score}/100
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Confidence
              </h4>
              <p className="text-lg font-bold text-blue-600">
                {Math.round(confidence * 100)}%
              </p>
            </div>
          </div>

          {/* Urgency Explanation */}
          <p className="text-xs text-slate-500 italic">{urgency.explanation}</p>

          {/* Eco Alternative */}
          {ecoAlternative && (
            <div className="rounded-lg bg-green-50 border border-green-200 p-3">
              <h4 className="text-xs font-semibold text-green-700 mb-1">
                🌱 Eco Alternative Available
              </h4>
              <p className="text-sm text-green-800 font-medium">
                {ecoAlternative.alternative_product_name}
              </p>
              <p className="text-xs text-green-600 mt-0.5">
                Saves {ecoAlternative.carbon_saved.toFixed(1)} kg CO₂ •
                Eco Score: {ecoAlternative.sustainability_score.toFixed(0)}/100
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
