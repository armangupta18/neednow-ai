"use client";

import { useEffect } from "react";
import { useMemory } from "@/hooks/useMemory";
import { LoadingSpinner, EmptyState } from "@/components/shared";
import { BUDGET_LABELS } from "@/types/memory";
import { formatRelativeTime } from "@/lib/utils";

export default function MemoryPage() {
  const {
    memory,
    isLoaded,
    lastUpdated,
    fetchMemory,
    removeDietaryPreference,
    removePreferredBrand,
    clearMemory,
  } = useMemory();

  useEffect(() => {
    fetchMemory();
  }, [fetchMemory]);

  if (!isLoaded) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" showLabel label="Loading preferences..." />
      </div>
    );
  }

  const isEmpty =
    memory.dietary_preferences.length === 0 &&
    memory.preferred_brands.length === 0 &&
    !memory.budget_level &&
    !memory.family_size;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">🧬 Memory Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Your learned preferences and shopping patterns.
            {lastUpdated && (
              <span className="ml-2 text-slate-400">
                Updated {formatRelativeTime(lastUpdated)}
              </span>
            )}
          </p>
        </div>
        {!isEmpty && (
          <button
            onClick={clearMemory}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50"
          >
            Reset Memory
          </button>
        )}
      </div>

      {isEmpty ? (
        <EmptyState
          icon="🧠"
          title="No preferences saved yet"
          description="As you shop, NeedNow AI will learn your dietary needs, favorite brands, and budget preferences."
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          {/* Dietary Preferences */}
          <MemorySection title="🥗 Dietary Preferences" empty={memory.dietary_preferences.length === 0}>
            <div className="flex flex-wrap gap-2">
              {memory.dietary_preferences.map((pref) => (
                <Tag key={pref} label={pref} onRemove={() => removeDietaryPreference(pref)} />
              ))}
            </div>
          </MemorySection>

          {/* Preferred Brands */}
          <MemorySection title="⭐ Preferred Brands" empty={memory.preferred_brands.length === 0}>
            <div className="flex flex-wrap gap-2">
              {memory.preferred_brands.map((brand) => (
                <Tag key={brand} label={brand} onRemove={() => removePreferredBrand(brand)} />
              ))}
            </div>
          </MemorySection>

          {/* Budget */}
          <MemorySection title="💰 Budget Level" empty={!memory.budget_level}>
            {memory.budget_level && (
              <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
                {BUDGET_LABELS[memory.budget_level]}
              </span>
            )}
          </MemorySection>

          {/* Family */}
          <MemorySection title="👨‍👩‍👧‍👦 Family Size" empty={!memory.family_size}>
            {memory.family_size && (
              <span className="text-lg font-bold text-slate-700">{memory.family_size} members</span>
            )}
          </MemorySection>

          {/* Sustainability */}
          <MemorySection title="🌱 Sustainability Score" empty={memory.sustainability_score === 0}>
            <div className="flex items-center gap-3">
              <div className="h-3 flex-1 rounded-full bg-slate-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-green-500 transition-all"
                  style={{ width: `${memory.sustainability_score}%` }}
                />
              </div>
              <span className="text-sm font-bold text-slate-700">{memory.sustainability_score.toFixed(0)}%</span>
            </div>
          </MemorySection>

          {/* Purchase Patterns */}
          <MemorySection title="📊 Purchase Patterns" empty={memory.purchase_patterns.length === 0}>
            <ul className="space-y-1">
              {memory.purchase_patterns.slice(0, 5).map((pattern, i) => (
                <li key={i} className="text-sm text-slate-600">• {pattern}</li>
              ))}
            </ul>
          </MemorySection>
        </div>
      )}
    </div>
  );
}

function MemorySection({ title, children, empty }: { title: string; children: React.ReactNode; empty: boolean }) {
  if (empty) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>
      {children}
    </div>
  );
}

function Tag({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700">
      {label}
      <button onClick={onRemove} className="text-slate-400 hover:text-red-500 ml-0.5" aria-label={`Remove ${label}`}>
        ×
      </button>
    </span>
  );
}
