"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useCart } from "@/hooks/useCart";
import { CartItemRow, CartSummary } from "@/components/cart";
import { EmptyState, LoadingSpinner } from "@/components/shared";
import { ROUTES } from "@/constants/routes";

export default function CartPage() {
  const { items, totalAmount, itemCount, loading, error, fetchCart, removeItem, emptyCart } = useCart();

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Your Cart</h1>
        <Link href={ROUTES.CHAT} className="text-sm text-blue-600 hover:underline">
          ← Back to Chat
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {loading && items.length === 0 ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner size="lg" showLabel label="Loading cart..." />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon="🛒"
          title="Your cart is empty"
          description="Start a conversation and we'll recommend products for you."
          actionLabel="Go to Chat"
          onAction={() => window.location.href = ROUTES.CHAT}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Items */}
          <div className="lg:col-span-2 space-y-2">
            {items.map((item) => (
              <CartItemRow key={item.id} item={item} onRemove={removeItem} loading={loading} />
            ))}
          </div>
          {/* Summary */}
          <div>
            <CartSummary
              totalAmount={totalAmount}
              itemCount={itemCount}
              onClear={emptyCart}
              loading={loading}
            />
          </div>
        </div>
      )}
    </div>
  );
}
