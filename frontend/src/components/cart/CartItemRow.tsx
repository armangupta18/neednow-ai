"use client";

import { formatPrice } from "@/lib/utils";
import type { CartItem } from "@/types/cart";

interface CartItemRowProps {
  item: CartItem;
  onRemove: (productId: string) => void;
  loading?: boolean;
}

export default function CartItemRow({ item, onRemove, loading }: CartItemRowProps) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-100 bg-white p-4 transition hover:border-slate-200">
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-slate-800 truncate">{item.product_name}</h4>
        <p className="text-xs text-slate-500 mt-0.5">
          {formatPrice(item.unit_price)} × {item.quantity}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <p className="text-sm font-bold text-slate-900">{formatPrice(item.line_total)}</p>
        <button
          onClick={() => onRemove(item.product_id)}
          disabled={loading}
          className="rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-500 disabled:opacity-50"
          aria-label="Remove item"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
