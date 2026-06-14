"use client";

import { useState } from "react";

interface EmergencyInputProps {
  onSubmit: (text: string) => void;
  loading?: boolean;
}

export default function EmergencyInput({ onSubmit, loading }: EmergencyInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    if (!value.trim() || loading) return;
    onSubmit(value.trim());
  };

  return (
    <div className="space-y-3">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Describe your emergency situation in detail..."
        disabled={loading}
        className="w-full rounded-xl border-2 border-red-200 bg-white p-4 text-sm leading-relaxed outline-none transition focus:border-red-400 focus:ring-4 focus:ring-red-100 disabled:opacity-50 min-h-[120px] resize-none"
      />
      <button
        onClick={handleSubmit}
        disabled={!value.trim() || loading}
        className="w-full rounded-xl bg-red-600 px-6 py-3 text-base font-bold text-white shadow-lg transition hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed animate-pulse-glow"
      >
        {loading ? "Analyzing..." : "🚨 Analyze Emergency"}
      </button>
    </div>
  );
}
