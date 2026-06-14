"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useUserStore } from "@/stores/user.store";
import { useMemory } from "@/hooks/useMemory";
import { useCartStore } from "@/stores/cart.store";
import { useChatStore } from "@/stores/chat.store";
import { ROUTES } from "@/constants/routes";
import { BUDGET_LABELS } from "@/types/memory";
import type { BudgetLevel } from "@/types/memory";

export default function ProfilePage() {
  const userId = useUserStore((s) => s.userId);
  const profile = useUserStore((s) => s.profile);
  const cartItemCount = useCartStore((s) => s.items.reduce((sum, i) => sum + i.quantity, 0));
  const messageCount = useChatStore((s) => s.messages.length);
  const { memory, isLoaded, fetchMemory, setBudgetLevel, setFamilySize } = useMemory();

  useEffect(() => {
    fetchMemory();
  }, [fetchMemory]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-900 text-2xl text-white font-bold">
          {(profile?.name ?? "U").charAt(0)}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{profile?.name ?? "NeedNow User"}</h1>
          <p className="text-sm text-slate-500">User ID: {userId.slice(0, 8)}...</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Messages" value={messageCount.toString()} icon="💬" />
        <StatCard label="Cart Items" value={cartItemCount.toString()} icon="🛒" />
        <StatCard label="Eco Score" value={`${memory.sustainability_score.toFixed(0)}`} icon="🌱" />
      </div>

      {/* Preferences Editor */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Preferences</h2>
        <div className="space-y-4">
          {/* Budget */}
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">Budget Level</label>
            <div className="flex gap-2">
              {(Object.keys(BUDGET_LABELS) as BudgetLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => setBudgetLevel(level)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                    memory.budget_level === level
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {BUDGET_LABELS[level]}
                </button>
              ))}
            </div>
          </div>

          {/* Family size */}
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">Family Size</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5, 6].map((size) => (
                <button
                  key={size}
                  onClick={() => setFamilySize(size)}
                  className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition ${
                    memory.family_size === size
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Quick links */}
      <div className="flex gap-3">
        <Link
          href={ROUTES.MEMORY}
          className="flex-1 rounded-lg border border-slate-200 px-4 py-3 text-center text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          🧬 View Full Memory
        </Link>
        <Link
          href={ROUTES.SUSTAINABILITY}
          className="flex-1 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-center text-sm font-medium text-green-700 transition hover:bg-green-100"
        >
          🌱 Sustainability
        </Link>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
      <span className="text-xl">{icon}</span>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
