"use client";

import { useState } from "react";
import { formatPrice } from "@/lib/utils";
import { ShoppingCart, Check, Loader2, Plus, Sparkles, Zap, ChevronDown, ChevronUp } from "lucide-react";

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
  onAddToCart: (productId: string) => Promise<boolean | void> | void;
  onBuyNow: () => void;
}

const DEFAULT_VISIBLE = 4;

export default function ProductCards({
  products,
  onAddToCart,
  onBuyNow,
}: ProductCardsProps) {
  const [expanded, setExpanded] = useState(false);
  const [addingId, setAddingId] = useState<string | null>(null);
  const [addedIds, setAddedIds] = useState<Record<string, boolean>>({});
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [floatingParticles, setFloatingParticles] = useState<Record<string, number>>({});
  const [topPickAdding, setTopPickAdding] = useState(false);
  const [topPickAdded, setTopPickAdded] = useState(false);

  if (!products || products.length === 0) return null;

  const visibleProducts = expanded ? products : products.slice(0, DEFAULT_VISIBLE);
  const hasMore = products.length > DEFAULT_VISIBLE;

  const handleItemAdd = async (product: ChatProduct) => {
    if (addingId) return;
    setAddingId(product.id);
    setHighlightedId(product.id);
    
    // Spawn floating +1 badge
    setFloatingParticles((prev) => ({ ...prev, [product.id]: (prev[product.id] || 0) + 1 }));

    try {
      await onAddToCart(product.id);
      setAddedIds((prev) => ({ ...prev, [product.id]: true }));
    } catch {
      // ignore
    } finally {
      setAddingId(null);
      
      // Auto clear highlight
      setTimeout(() => {
        setHighlightedId((curr) => (curr === product.id ? null : curr));
      }, 1500);

      // Auto revert added button text after 2.5s
      setTimeout(() => {
        setAddedIds((prev) => ({ ...prev, [product.id]: false }));
      }, 2500);
    }
  };

  const handleTopPickAdd = async () => {
    const topProduct = products[0];
    if (!topProduct || topPickAdding) return;

    setTopPickAdding(true);
    setHighlightedId(topProduct.id);
    setFloatingParticles((prev) => ({ ...prev, [topProduct.id]: (prev[topProduct.id] || 0) + 1 }));

    try {
      await onAddToCart(topProduct.id);
      setTopPickAdded(true);
      setAddedIds((prev) => ({ ...prev, [topProduct.id]: true }));
    } catch {
      // ignore
    } finally {
      setTopPickAdding(false);

      setTimeout(() => {
        setHighlightedId((curr) => (curr === topProduct.id ? null : curr));
      }, 1500);

      setTimeout(() => {
        setTopPickAdded(false);
        setAddedIds((prev) => ({ ...prev, [topProduct.id]: false }));
      }, 2500);
    }
  };

  return (
    <div className="mt-3 space-y-2">
      {visibleProducts.map((product, idx) => {
        const isAdding = addingId === product.id;
        const isAdded = !!addedIds[product.id];
        const isHighlighted = highlightedId === product.id;
        const particleCount = floatingParticles[product.id] || 0;

        return (
          <div
            key={product.id}
            className={`relative rounded-xl border p-3 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-bottom-1
              ${isHighlighted 
                ? "border-emerald-500 bg-emerald-50/40 shadow-md ring-2 ring-emerald-400/40 scale-[1.01]" 
                : "border-slate-200 bg-gradient-to-r from-white to-slate-50 hover:border-slate-300 hover:shadow"
              }`}
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            {/* Floating +1 animation bubble */}
            {particleCount > 0 && (
              <div
                key={particleCount}
                className="pointer-events-none absolute -top-2 right-4 z-20 flex items-center gap-1 rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-bold text-white shadow-lg animate-float-up"
              >
                <Sparkles className="h-3 w-3" />
                <span>+1 Added</span>
              </div>
            )}

            <div className="flex items-start gap-3">
              {/* Product rank badge */}
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-bold transition-colors duration-300
                  ${isHighlighted 
                    ? "bg-emerald-100 text-emerald-700" 
                    : idx < 4 
                      ? "bg-blue-50 text-blue-600" 
                      : "bg-slate-100 text-slate-500"}`}
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

              {/* Add to cart button with animated state */}
              <button
                type="button"
                onClick={() => handleItemAdd(product)}
                disabled={isAdding}
                className={`relative shrink-0 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition-all duration-200 active:scale-95
                  ${isAdded
                    ? "bg-emerald-600 text-white hover:bg-emerald-700 ring-2 ring-emerald-500/20"
                    : isAdding
                      ? "bg-slate-700 text-slate-200 cursor-not-allowed opacity-90"
                      : "bg-slate-900 text-white hover:bg-slate-800 hover:shadow hover:-translate-y-0.5"
                  }`}
              >
                {isAdding ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Adding...</span>
                  </>
                ) : isAdded ? (
                  <>
                    <Check className="h-3.5 w-3.5 animate-checkmark-pop" />
                    <span className="animate-in fade-in duration-200">Added!</span>
                  </>
                ) : (
                  <>
                    <Plus className="h-3.5 w-3.5" />
                    <span>Cart</span>
                  </>
                )}
              </button>
            </div>
          </div>
        );
      })}

      {/* View More / Show Less toggle */}
      {hasMore && (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex w-full items-center justify-center gap-1 rounded-lg border border-slate-200 bg-slate-50 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-800 transition-all active:scale-[0.99]"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3.5 w-3.5" />
              <span>Show Less</span>
            </>
          ) : (
            <>
              <ChevronDown className="h-3.5 w-3.5" />
              <span>View More ({products.length - DEFAULT_VISIBLE} more)</span>
            </>
          )}
        </button>
      )}

      {/* Buy Now / Add Top Pick buttons with rich animations */}
      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={handleTopPickAdd}
          disabled={topPickAdding}
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2.5 px-3 text-xs font-semibold shadow-sm transition-all duration-200 active:scale-95
            ${topPickAdded
              ? "bg-emerald-600 text-white shadow-emerald-200"
              : topPickAdding
                ? "bg-blue-500 text-blue-100 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md hover:-translate-y-0.5"
            }`}
        >
          {topPickAdding ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>Adding Top Pick...</span>
            </>
          ) : topPickAdded ? (
            <>
              <Check className="h-3.5 w-3.5 animate-checkmark-pop" />
              <span className="animate-in fade-in duration-200">✓ Top Pick Added!</span>
            </>
          ) : (
            <>
              <ShoppingCart className="h-3.5 w-3.5" />
              <span>Add Top Pick to Cart</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onBuyNow}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-green-600 py-2.5 px-3 text-xs font-semibold text-white shadow-sm hover:bg-green-700 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
        >
          <Zap className="h-3.5 w-3.5 fill-current" />
          <span>Buy Now</span>
        </button>
      </div>
    </div>
  );
}
