"use client";

import Link from "next/link";
import { useChat } from "@/hooks/useChat";
import { useCart } from "@/hooks/useCart";
import { ProductCard } from "@/components/cart";
import { EcoAlternativeCard } from "@/components/sustainability";
import { EmptyState } from "@/components/shared";
import { ROUTES } from "@/constants/routes";
import { URGENCY_CONFIG } from "@/constants/emergency";
import type { UrgencyLevel } from "@/constants/emergency";
import { cn } from "@/lib/utils";

export default function RecommendationsPage() {
  const { lastResult } = useChat();
  const { addItem } = useCart();

  if (!lastResult) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Recommendations</h1>
        <EmptyState
          icon="🛒"
          title="No recommendations yet"
          description="Start a conversation to get personalized product suggestions."
          actionLabel="Start Shopping"
          onAction={() => window.location.href = ROUTES.CHAT}
        />
      </div>
    );
  }

  const { cart, urgency, reasoning, ecoAlternative, confidence } = lastResult;
  const urgencyConfig = URGENCY_CONFIG[urgency.level as UrgencyLevel] ?? URGENCY_CONFIG.LOW;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
          <p className="text-sm text-slate-500 mt-1">
            Category: <span className="font-medium capitalize">{cart.category}</span> •
            Confidence: <span className="font-medium">{Math.round(confidence * 100)}%</span>
          </p>
        </div>
        <span className={cn("rounded-full px-3 py-1 text-xs font-semibold", urgencyConfig.bgColor, urgencyConfig.color)}>
          {urgencyConfig.icon} {urgencyConfig.label}
        </span>
      </div>

      {/* Reasoning */}
      <div className="mb-6 rounded-lg border bg-slate-50 p-4">
        <p className="text-sm text-slate-700">🧠 {reasoning}</p>
      </div>

      {/* Products */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Top Products ({cart.products.slice(0, 4).length})
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-2">
          {cart.products.slice(0, 4).map((product) => (
            <ProductCard
              key={product.id}
              id={product.id}
              title={product.title}
              price={product.price}
              score={product.score}
              onAddToCart={addItem}
            />
          ))}
        </div>
      </section>

      {/* Bundles */}
      {cart.bundles.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            📦 Bundle Suggestions ({cart.bundles.length})
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {cart.bundles.map((product) => (
              <ProductCard
                key={product.id}
                id={product.id}
                title={product.title}
                price={product.price}
                onAddToCart={addItem}
              />
            ))}
          </div>
        </section>
      )}

      {/* Eco Alternative */}
      {ecoAlternative && (
        <section>
          <h2 className="text-lg font-semibold text-green-800 mb-4">🌱 Eco-Friendly Alternative</h2>
          <EcoAlternativeCard
            originalName={ecoAlternative.original_product_name}
            alternativeName={ecoAlternative.alternative_product_name}
            carbonSaved={ecoAlternative.carbon_saved}
            priceDifference={ecoAlternative.price_difference}
            sustainabilityScore={ecoAlternative.sustainability_score}
          />
        </section>
      )}

      {/* CTA */}
      <div className="mt-8 flex gap-3">
        <Link
          href={ROUTES.CART}
          className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-slate-800"
        >
          View Cart →
        </Link>
        <Link
          href={ROUTES.CHAT}
          className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Continue Shopping
        </Link>
      </div>
    </div>
  );
}
