"use client";

import { cn } from "@/lib/utils";
import { formatPrice } from "@/lib/utils";

interface ProductCardProps {
  id: string;
  title: string;
  price: number;
  score?: number;
  category?: string;
  onAddToCart?: (id: string) => void;
  isInCart?: boolean;
  loading?: boolean;
}

export default function ProductCard({
  id,
  title,
  price,
  score,
  category,
  onAddToCart,
  isInCart,
  loading,
}: ProductCardProps) {
  return (
    <div className="group rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md hover:border-blue-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-slate-800 line-clamp-2">{title}</h4>
          {category && (
            <span className="mt-1 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
              {category}
            </span>
          )}
        </div>
        {score !== undefined && (
          <div className="shrink-0 text-right">
            <span className="text-xs text-slate-400">Match</span>
            <p className="text-sm font-bold text-blue-600">{score.toFixed(0)}%</p>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <p className="text-lg font-bold text-slate-900">{formatPrice(price)}</p>
        {onAddToCart && (
          <button
            onClick={() => onAddToCart(id)}
            disabled={isInCart || loading}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
              isInCart
                ? "bg-green-100 text-green-700 cursor-default"
                : "bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50"
            )}
          >
            {isInCart ? "✓ In Cart" : loading ? "Adding..." : "Add to Cart"}
          </button>
        )}
      </div>
    </div>
  );
}
