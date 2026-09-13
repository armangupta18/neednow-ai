"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface ProductReasoning {
  product_name: string;
  reason: string;
}

interface ReasoningPanelProps {
  reasoning: string;
  urgency?: { level: string; score: number; explanation: string } | null;
  confidence: number;
  productReasonings?: ProductReasoning[];
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
  productReasonings = [],
  ecoAlternative,
}: ReasoningPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const showUrgency =
    !!urgency && typeof urgency === "object" && urgency.level !== "STANDARD";

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
          {/* Confidence badge */}
          <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-600">
            {Math.round(confidence * 100)}% confidence
          </span>
        </div>
        <span className="text-xs text-slate-400">
          {expanded ? "▲ Collapse" : "▼ Expand"}
        </span>
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="border-t px-4 py-4 space-y-4 animate-fade-in">

          {/* Per-product reasoning items (structured, from combined synthesis) */}
          {productReasonings.length > 0 ? (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
                Why These Products
              </h4>
              <ul className="space-y-2">
                {productReasonings.map((item, i) => (
                  <li key={i} className="rounded-lg bg-slate-50 px-3 py-2">
                    <p className="text-xs font-semibold text-slate-800">
                      {i + 1}. {item.product_name}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.reason}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            /* Fallback: plain reasoning string */
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Reasoning
              </h4>
              <p className="text-sm text-slate-700 leading-relaxed">{reasoning}</p>
            </div>
          )}

          {/* Urgency details — only shown when urgency agent is enabled */}
          {showUrgency && urgency && typeof urgency === "object" && (
            <>
              <div className="flex gap-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                    Urgency Score
                  </h4>
                  <p className="text-lg font-bold text-orange-600">
                    {urgency.score}/100
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                    Level
                  </h4>
                  <p className="text-lg font-bold text-slate-700">
                    {urgency.level}
                  </p>
                </div>
              </div>
              {urgency.explanation && (
                <p className="text-xs text-slate-500 italic">{urgency.explanation}</p>
              )}
            </>
          )}

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
