"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useUserStore } from "@/stores/user.store";
import { getOrder } from "@/services/order.service";
import { ROUTES } from "@/constants/routes";
import { formatPrice } from "@/lib/utils";
import type { OrderResponse } from "@/types/order";

export default function OrderSuccessPage() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("orderId");
  const userId = useUserStore((s) => s.userId);

  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderId) {
      setLoading(false);
      return;
    }

    async function fetchOrder() {
      try {
        setLoading(true);
        const data = await getOrder(userId, orderId!);
        setOrder(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load order details");
      } finally {
        setLoading(false);
      }
    }

    fetchOrder();
  }, [orderId, userId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-green-600 border-t-transparent" />
        <p className="mt-3 text-sm text-slate-500">Loading order details...</p>
      </div>
    );
  }

  if (error || !orderId) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <span className="text-5xl mb-4 block">⚠️</span>
        <h2 className="text-xl font-semibold text-slate-800 mb-2">
          {error || "No order ID found"}
        </h2>
        <Link
          href={ROUTES.CHAT}
          className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 sm:px-6 py-12">
      {/* Success Header */}
      <div className="text-center mb-8">
        <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
          <span className="text-4xl">✓</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Order Placed Successfully!</h1>
        <p className="text-slate-500">Your order has been confirmed and will be delivered soon.</p>
      </div>

      {/* Order Details Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <DetailRow label="Order ID" value={orderId} highlight />
          <DetailRow label="Status" value={order?.status === "confirmed" ? "✓ Confirmed" : (order?.status || "Confirmed")} />
          <DetailRow label="Payment Method" value={formatPaymentMethod(order?.payment_method || "cod")} />
          <DetailRow label="Total Amount" value={formatPrice(order?.total_amount || 0)} />
        </div>

        {order?.estimated_delivery && (
          <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
            <p className="text-sm font-medium text-blue-800">
              🚀 Estimated Delivery: {order.estimated_delivery}
            </p>
          </div>
        )}

        {/* Delivery Address */}
        {order?.address && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Delivery Address</h3>
            <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
              <p className="font-medium text-slate-800">{order.address.name}</p>
              <p>{order.address.address}</p>
              {order.address.landmark && <p>{order.address.landmark}</p>}
              <p>{order.address.city}, {order.address.state} - {order.address.pincode}</p>
              <p>📞 {order.address.phone}</p>
            </div>
          </div>
        )}

        {/* Items */}
        {order?.items && order.items.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Items ({order.items.length})</h3>
            <div className="space-y-2">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex justify-between text-sm rounded-lg bg-slate-50 p-3">
                  <span className="text-slate-700">
                    {item.product_name} × {item.quantity}
                  </span>
                  <span className="font-medium text-slate-900">
                    {formatPrice(item.unit_price * item.quantity)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href={ROUTES.CHAT}
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white text-center hover:bg-blue-700 transition-colors"
        >
          Continue Shopping
        </Link>
        <Link
          href={ROUTES.ORDERS}
          className="rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 text-center hover:bg-slate-50 transition-colors"
        >
          View Orders
        </Link>
      </div>
    </div>
  );
}

function DetailRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={highlight ? "font-mono font-bold text-slate-900" : "font-medium text-slate-800"}>
        {value}
      </p>
    </div>
  );
}

function formatPaymentMethod(method: string): string {
  const map: Record<string, string> = {
    cod: "Cash on Delivery",
    upi: "UPI",
    credit_card: "Credit Card",
    debit_card: "Debit Card",
    net_banking: "Net Banking",
  };
  return map[method] || method;
}
