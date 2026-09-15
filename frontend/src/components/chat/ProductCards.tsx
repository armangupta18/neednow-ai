"use client";

import { useState } from "react";
import { formatPrice } from "@/lib/utils";

interface ChatProduct {
  id: string;
  title: string;
  price: number;
  score?: number;
  reason?: string;
  priority?: number;
}

interface ProductCardsProps {
  products: ChatProduct[];
  onAddToCart: (productId: string) => void;
  onBuyNow: () => void;
}

const DEFAULT_VISIBLE = 4;

export default function ProductCards({
  products,
  onAddToCart,
  onBuyNow,
}: ProductCardsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!products || products.length === 0) return null;

  const visibleProducts = expanded ? products : products.slice(0, DEFAULT_VISIBLE);
  const hasMore = products.length > DEFAULT_VISIBLE;

  return (
    <div className="mt-3 space-y-2">
      {visibleProducts.map((product, idx) => (
        <div
          key={product.id}
          className="rounded-xl border border-slate-200 bg-gradient-to-r from-white to-slate-50 p-3 shadow-sm transition-all animate-in fade-in slide-in-from-bottom-1 duration-200"
          style={{ animationDelay: `${idx * 40}ms` }}
        >
          <div className="flex items-start gap-3">
            {/* Product rank badge */}
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold
                ${idx < 4 ? "bg-blue-50 text-blue-600" : "bg-slate-100 text-slate-500"}`}
            >
              {product.priority ?? idx + 1}
            </div>

            {/* Product info */}
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-slate-900 line-clamp-2">
                {product.title}
              </h4>
              <div className="mt-1 flex items-center gap-3">
                <span className="text-base font-bold text-slate-900">
                  {formatPrice(product.price)}
                </span>
                {product.score != null && product.score > 0 && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
                    {Math.round(product.score * 100)}% match
                  </span>
                )}
              </div>
              {product.reason && product.reason !== "Also relevant to your search" && (
                <p className="mt-1 text-xs text-slate-500 line-clamp-1">
                  {product.reason}
                </p>
              )}
            </div>

            {/* Add to cart button */}
            <button
              onClick={() => onAddToCart(product.id)}
              className="shrink-0 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
            >
              + Cart
            </button>
          </div>
        </div>
      ))}

      {/* View More / Show Less toggle */}
      {hasMore && (
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
        >
          {expanded ? "▲ Show Less" : "▼ View More"}
        </button>
      )}

      {/* Buy Now / Add Top Pick */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={() => { if (products[0]) onAddToCart(products[0].id); }}
          className="flex-1 rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          🛒 Add Top Pick to Cart
        </button>
        <button
          onClick={onBuyNow}
          className="flex-1 rounded-lg bg-green-600 py-2 text-xs font-semibold text-white hover:bg-green-700 transition-colors"
        >
          ⚡ Buy Now
        </button>
      </div>
    </div>
  );
}
