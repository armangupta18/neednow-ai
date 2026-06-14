"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/hooks/useCart";
import { useCartStore } from "@/stores/cart.store";
import { ROUTES } from "@/constants/routes";
import { formatPrice, cn } from "@/lib/utils";

export default function CartPage() {
  const router = useRouter();
  const { items, totalAmount, itemCount, loading, error, fetchCart, removeItem, emptyCart } = useCart();
  const updateQuantity = useCartStore((s) => s.updateQuantity);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const deliveryFee = items.length > 0 ? 40 : 0;
  const platformFee = items.length > 0 ? 5 : 0;
  const tax = Math.round(totalAmount * 0.05);
  const totalPayable = totalAmount + deliveryFee + platformFee + tax;

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Your Cart</h1>
        <Link href={ROUTES.CHAT} className="text-sm text-blue-600 hover:underline">
          ← Back to Chat
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-sm text-slate-500">Loading cart...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4">🛒</span>
          <h2 className="text-xl font-semibold text-slate-800 mb-2">Your cart is empty</h2>
          <p className="text-slate-500 mb-6">Start a conversation and we&apos;ll recommend products for you.</p>
          <Link
            href={ROUTES.CHAT}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            Go to Chat
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-xl">
                  📦
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-slate-900 truncate">{item.product_name}</h3>
                  <p className="text-sm text-slate-500">{formatPrice(item.unit_price)} each</p>
                </div>

                {/* Quantity Controls */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (item.quantity <= 1) {
                        removeItem(item.product_id);
                      } else {
                        updateQuantity(item.product_id, item.quantity - 1);
                      }
                    }}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-100 transition-colors"
                    aria-label="Decrease quantity"
                  >
                    −
                  </button>
                  <span className="w-8 text-center text-sm font-medium text-slate-900">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-100 transition-colors"
                    aria-label="Increase quantity"
                  >
                    +
                  </button>
                </div>

                {/* Line Total */}
                <div className="text-right min-w-[80px]">
                  <p className="font-semibold text-slate-900">{formatPrice(item.line_total)}</p>
                </div>

                {/* Remove */}
                <button
                  onClick={() => removeItem(item.product_id)}
                  className="text-red-500 hover:text-red-700 transition-colors p-1"
                  aria-label={`Remove ${item.product_name}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            ))}

            <button
              onClick={emptyCart}
              disabled={loading}
              className="mt-2 text-sm text-red-600 hover:text-red-700 hover:underline disabled:opacity-50"
            >
              Clear Cart
            </button>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sticky top-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Order Summary</h2>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-slate-600">
                  <span>Subtotal ({itemCount} items)</span>
                  <span>{formatPrice(totalAmount)}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Delivery Fee</span>
                  <span>{formatPrice(deliveryFee)}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Platform Fee</span>
                  <span>{formatPrice(platformFee)}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Tax (5%)</span>
                  <span>{formatPrice(tax)}</span>
                </div>
                <div className="border-t border-slate-200 pt-3">
                  <div className="flex justify-between font-semibold text-slate-900">
                    <span>Total Payable</span>
                    <span>{formatPrice(totalPayable)}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => router.push(ROUTES.CHECKOUT)}
                disabled={loading || items.length === 0}
                className={cn(
                  "mt-6 w-full rounded-lg py-3 text-sm font-semibold text-white transition-colors",
                  "bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
                )}
              >
                Proceed to Checkout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
