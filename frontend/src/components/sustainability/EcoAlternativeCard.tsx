"use client";

import { formatCarbonSaved } from "@/services/sustainability.service";
import { formatPrice } from "@/lib/utils";

interface EcoAlternativeCardProps {
  originalName: string;
  alternativeName: string;
  carbonSaved: number;
  priceDifference: number;
  sustainabilityScore: number;
}

export default function EcoAlternativeCard({
  originalName,
  alternativeName,
  carbonSaved,
  priceDifference,
  sustainabilityScore,
}: EcoAlternativeCardProps) {
  return (
    <div className="rounded-xl border border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-slate-500">Instead of <span className="font-medium">{originalName}</span></p>
          <h4 className="mt-1 text-sm font-bold text-green-800">{alternativeName}</h4>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-700">
          {sustainabilityScore.toFixed(0)}
        </div>
      </div>
      <div className="mt-3 flex gap-4 text-xs">
        {carbonSaved > 0 ? (
          <span className="text-green-700 font-medium">🌱 {formatCarbonSaved(carbonSaved)}</span>
        ) : (
          <span className="text-slate-500 font-medium">🌱 Carbon impact data unavailable</span>
        )}
        <span className="text-slate-600">
          {priceDifference > 0 ? `+${formatPrice(priceDifference)}` : formatPrice(Math.abs(priceDifference)) + " cheaper"}
        </span>
      </div>
    </div>
  );
}
