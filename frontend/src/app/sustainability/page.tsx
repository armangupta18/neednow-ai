"use client";

import { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { useSustainability } from "@/hooks/useSustainability";
import { EcoScoreBadge, EcoAlternativeCard } from "@/components/sustainability";
import { EmptyState, LoadingSpinner } from "@/components/shared";
import { MODEL_CONFIG } from "@/constants/agent-config";
import type { SustainabilityRecommendResponse } from "@/services/sustainability.service";

export default function SustainabilityPage() {
  const { lastResult } = useChat();
  const { loading, error, getRecommendations } = useSustainability();
  const [report, setReport] = useState<SustainabilityRecommendResponse | null>(null);

  const productIds = lastResult?.cart.products.map((p) => p.id) ?? [];

  const handleAnalyze = async () => {
    if (productIds.length === 0) return;
    const result = await getRecommendations(productIds);
    if (result) setReport(result);
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">🌱 Sustainability Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Discover eco-friendly alternatives and track your carbon savings.
        </p>
      </div>

      {/* Stats bar */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Products Indexed" value={MODEL_CONFIG.VECTOR_STORE.totalProducts.toLocaleString()} />
        <StatCard label="Eco Alternatives" value={report?.recommendations.length.toString() ?? "—"} />
        <StatCard label="Carbon Saved" value={report ? `${report.total_carbon_saved.toFixed(1)} kg` : "—"} />
        <StatCard label="Overall Score" value={report ? `${report.overall_sustainability_score.toFixed(0)}/100` : "—"} />
      </div>

      {/* Analyze button */}
      {productIds.length > 0 && !report && (
        <div className="mb-8 text-center">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="rounded-lg bg-green-600 px-6 py-3 text-sm font-semibold text-white shadow transition hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : `🔍 Analyze ${productIds.length} Products`}
          </button>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" color="primary" showLabel label="Analyzing sustainability..." />
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {/* Report */}
      {report && report.recommendations.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-green-800">Eco-Friendly Alternatives</h2>
            <EcoScoreBadge score={report.overall_sustainability_score} size="md" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {report.recommendations.map((alt, i) => (
              <EcoAlternativeCard
                key={i}
                originalName={alt.original_product_name}
                alternativeName={alt.alternative_product_name}
                carbonSaved={alt.carbon_saved}
                priceDifference={alt.price_difference}
                sustainabilityScore={alt.sustainability_score}
              />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {!loading && !report && productIds.length === 0 && (
        <EmptyState
          icon="🌱"
          title="No products to analyze"
          description="Start a shopping conversation first, then come here to see eco-friendly alternatives."
        />
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{label}</p>
    </div>
  );
}
