"use client";

import { cn } from "@/lib/utils";
import { getSustainabilityLabel, getSustainabilityColor } from "@/services/sustainability.service";

interface EcoScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export default function EcoScoreBadge({ score, size = "md" }: EcoScoreBadgeProps) {
  const label = getSustainabilityLabel(score);
  const color = getSustainabilityColor(score);
  const sizes = { sm: "h-10 w-10 text-xs", md: "h-14 w-14 text-sm", lg: "h-20 w-20 text-lg" };

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={cn(
          "flex items-center justify-center rounded-full border-2 font-bold",
          sizes[size],
          color,
          score >= 60 ? "border-green-300 bg-green-50" : "border-slate-200 bg-slate-50"
        )}
      >
        {score.toFixed(0)}
      </div>
      <span className={cn("text-[10px] font-medium", color)}>{label}</span>
    </div>
  );
}
