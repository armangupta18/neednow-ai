"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useUserStore } from "@/stores/user.store";
import { getOrders } from "@/services/order.service";
import { ROUTES } from "@/constants/routes";
import { formatPrice, formatRelativeTime } from "@/lib/utils";
import type { OrderResponse } from "@/types/order";

export default function OrdersPage() {
  const userId = useUserStore((s) => s.userId);
  const [orders, setOrders] = useState<OrderResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOrders() {
      try {
        setLoading(true);
        setError(null);
        const data = await getOrders(userId);
        setOrders(data.orders);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load orders");
      } finally {
        setLoading(false);
      }
    }

    fetchOrders();
  }, [userId]);

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">My Orders</h1>
        <Link href={ROUTES.CHAT} className="text-sm text-blue-600 hover:underline">
          ← Continue Shopping
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="mt-3 text-sm text-slate-500">Loading orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="text-5xl mb-4">📋</span>
          <h2 className="text-xl font-semibold text-slate-800 mb-2">No orders yet</h2>
          <p className="text-slate-500 mb-6">Your order history will appear here once you place an order.</p>
          <Link
            href={ROUTES.CHAT}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            Start Shopping
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <Link
              key={order.order_id}
              href={`${ROUTES.ORDER_SUCCESS}?orderId=${order.order_id}`}
              className="block rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-mono text-sm font-bold text-slate-900">{order.order_id}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatRelativeTime(order.created_at)}
                  </p>
                </div>
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 capitalize">
                  {order.status}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-slate-600">
                  <span>📦 {order.items.length} item{order.items.length > 1 ? "s" : ""}</span>
                  <span>💳 {formatPaymentLabel(order.payment_method)}</span>
                </div>
                <p className="text-lg font-semibold text-slate-900">{formatPrice(order.total_amount)}</p>
              </div>

              {/* Item preview */}
              <div className="mt-3 flex flex-wrap gap-1">
                {order.items.slice(0, 3).map((item, idx) => (
                  <span
                    key={idx}
                    className="inline-block rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600"
                  >
                    {item.product_name}
                  </span>
                ))}
                {order.items.length > 3 && (
                  <span className="inline-block rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500">
                    +{order.items.length - 3} more
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function formatPaymentLabel(method: string): string {
  const map: Record<string, string> = {
    cod: "COD",
    upi: "UPI",
    credit_card: "Credit Card",
    debit_card: "Debit Card",
    net_banking: "Net Banking",
  };
  return map[method] || method;
}
