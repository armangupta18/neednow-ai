"use client";

import { SITUATION_EXAMPLES } from "@/constants/prompts";

interface SuggestionsProps {
  onSelect: (suggestion: string) => void;
  visible?: boolean;
}

export default function Suggestions({ onSelect, visible = true }: SuggestionsProps) {
  if (!visible) return null;

  return (
    <div className="animate-fade-in">
      <p className="text-xs font-medium text-slate-500 mb-2">💡 Try one of these:</p>
      <div className="flex flex-wrap gap-2">
        {SITUATION_EXAMPLES.map((example) => (
          <button
            key={example}
            onClick={() => onSelect(example)}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 shadow-sm transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
          >
            {example.length > 50 ? example.slice(0, 50) + "…" : example}
          </button>
        ))}
      </div>
    </div>
  );
}
