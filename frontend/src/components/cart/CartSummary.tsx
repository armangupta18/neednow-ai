"use client";

import { formatPrice } from "@/lib/utils";

interface CartSummaryProps {
  totalAmount: number;
  itemCount: number;
  onClear: () => void;
  onCheckout?: () => void;
  loading?: boolean;
}

export default function CartSummary({ totalAmount, itemCount, onClear, onCheckout, loading }: CartSummaryProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">Order Summary</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between text-slate-600">
          <span>Items ({itemCount})</span>
          <span>{formatPrice(totalAmount)}</span>
        </div>
        <div className="flex justify-between text-slate-600">
          <span>Delivery</span>
          <span className="text-green-600 font-medium">Free</span>
        </div>
        <div className="border-t pt-2 flex justify-between font-bold text-slate-900">
          <span>Total</span>
          <span>{formatPrice(totalAmount)}</span>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {onCheckout && (
          <button
            onClick={onCheckout}
            className="w-full rounded-lg bg-slate-900 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-slate-800"
          >
            Proceed to Checkout
          </button>
        )}
        <button
          onClick={onClear}
          disabled={loading || itemCount === 0}
          className="w-full rounded-lg border border-slate-200 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
        >
          Clear Cart
        </button>
      </div>
    </div>
  );
}
