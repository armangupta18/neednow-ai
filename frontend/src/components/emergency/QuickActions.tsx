"use client";

const QUICK_SCENARIOS = [
  { icon: "💊", label: "Need medicine urgently", text: "I need my prescription medicine urgently, running out today" },
  { icon: "👶", label: "Baby emergency", text: "My baby has a high fever and needs medicine immediately" },
  { icon: "🩹", label: "First aid needed", text: "Someone got injured and I need a first aid kit right now" },
  { icon: "💉", label: "Insulin emergency", text: "Diabetic emergency - running out of insulin, need delivery immediately" },
  { icon: "🧓", label: "Elderly care", text: "My elderly parent needs adult diapers urgently, bedridden" },
  { icon: "🫁", label: "Breathing difficulty", text: "Asthma attack - need a nebulizer or inhaler delivered immediately" },
];

interface QuickActionsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export default function QuickActions({ onSelect, disabled }: QuickActionsProps) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-slate-700">⚡ Quick Emergency Scenarios</h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {QUICK_SCENARIOS.map((scenario) => (
          <button
            key={scenario.label}
            onClick={() => onSelect(scenario.text)}
            disabled={disabled}
            className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 text-left transition hover:border-red-300 hover:bg-red-50 disabled:opacity-50"
          >
            <span className="text-xl">{scenario.icon}</span>
            <span className="text-sm font-medium text-slate-700">{scenario.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
