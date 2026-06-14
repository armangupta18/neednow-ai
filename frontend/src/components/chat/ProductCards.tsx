"use client";

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

export default function ProductCards({
  products,
  onAddToCart,
  onBuyNow,
}: ProductCardsProps) {
  if (!products || products.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      {products.slice(0, 4).map((product, idx) => (
        <div
          key={product.id}
          className="rounded-xl border border-slate-200 bg-gradient-to-r from-white to-slate-50 p-3 shadow-sm"
        >
          <div className="flex items-start gap-3">
            {/* Product icon/number */}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-sm font-bold text-blue-600">
              {idx + 1}
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
                {product.score && product.score > 0 && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
                    {Math.round(product.score * 100)}% match
                  </span>
                )}
              </div>
              {product.reason && (
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

      {/* Buy Now button */}
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
