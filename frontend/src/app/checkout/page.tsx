"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useCartStore } from "@/stores/cart.store";
import { useUserStore } from "@/stores/user.store";
import { placeOrder } from "@/services/order.service";
import { ROUTES } from "@/constants/routes";
import { formatPrice, cn } from "@/lib/utils";
import { PAYMENT_METHODS } from "@/types/order";
import type { PaymentMethod, OrderAddress } from "@/types/order";

export default function CheckoutPage() {
  const router = useRouter();
  const userId = useUserStore((s) => s.userId);
  const { items, totalAmount, clearCart } = useCartStore();
  const itemCount = items.reduce((sum, i) => sum + i.quantity, 0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cod");
  const [upiConfirmed, setUpiConfirmed] = useState(false);

  // Address form
  const [address, setAddress] = useState<OrderAddress>({
    name: "",
    phone: "",
    address: "",
    landmark: "",
    city: "",
    state: "",
    pincode: "",
  });

  const [formErrors, setFormErrors] = useState<Partial<Record<keyof OrderAddress, string>>>({});

  const deliveryFee = 40;
  const platformFee = 5;
  const tax = Math.round(totalAmount * 0.05);
  const totalPayable = totalAmount + deliveryFee + platformFee + tax;

  function updateAddress(field: keyof OrderAddress, value: string) {
    setAddress((prev) => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  function validateForm(): boolean {
    const errors: Partial<Record<keyof OrderAddress, string>> = {};
    if (!address.name.trim()) errors.name = "Name is required";
    if (!address.phone.trim()) errors.phone = "Phone is required";
    else if (!/^\d{10}$/.test(address.phone.trim())) errors.phone = "Enter a valid 10-digit phone number";
    if (!address.address.trim()) errors.address = "Address is required";
    if (!address.city.trim()) errors.city = "City is required";
    if (!address.state.trim()) errors.state = "State is required";
    if (!address.pincode.trim()) errors.pincode = "Pincode is required";
    else if (!/^\d{6}$/.test(address.pincode.trim())) errors.pincode = "Enter a valid 6-digit pincode";

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handlePlaceOrder() {
    if (!validateForm()) return;
    if (paymentMethod === "upi" && !upiConfirmed) {
      setError("Please confirm UPI payment before placing the order.");
      return;
    }
    if (items.length === 0) {
      setError("Your cart is empty.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await placeOrder({
        user_id: userId,
        cart_items: items.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
        address,
        payment_method: paymentMethod,
        total_amount: totalPayable,
      });

      // Clear cart on both frontend and backend
      clearCart();
      try {
        const { clearCart: clearBackendCart } = await import("@/services/cart.service");
        await clearBackendCart(userId);
      } catch {
        // Non-critical: backend order service already clears cart
      }

      router.push(`${ROUTES.ORDER_SUCCESS}?orderId=${response.order_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to place order. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-16 text-center">
        <span className="text-5xl mb-4 block">🛒</span>
        <h2 className="text-xl font-semibold text-slate-800 mb-2">Your cart is empty</h2>
        <p className="text-slate-500 mb-6">Add items to your cart before checking out.</p>
        <Link
          href={ROUTES.CART}
          className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Go to Cart
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Checkout</h1>
        <Link href={ROUTES.CART} className="text-sm text-blue-600 hover:underline">
          ← Back to Cart
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Delivery Address */}
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">📍 Delivery Address</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <InputField
                label="Full Name"
                value={address.name}
                onChange={(v) => updateAddress("name", v)}
                error={formErrors.name}
                placeholder="John Doe"
              />
              <InputField
                label="Phone Number"
                value={address.phone}
                onChange={(v) => updateAddress("phone", v)}
                error={formErrors.phone}
                placeholder="9876543210"
                type="tel"
              />
              <div className="sm:col-span-2">
                <InputField
                  label="Address"
                  value={address.address}
                  onChange={(v) => updateAddress("address", v)}
                  error={formErrors.address}
                  placeholder="House no., Street, Area"
                />
              </div>
              <InputField
                label="Landmark (Optional)"
                value={address.landmark}
                onChange={(v) => updateAddress("landmark", v)}
                placeholder="Near..."
              />
              <InputField
                label="City"
                value={address.city}
                onChange={(v) => updateAddress("city", v)}
                error={formErrors.city}
                placeholder="Mumbai"
              />
              <InputField
                label="State"
                value={address.state}
                onChange={(v) => updateAddress("state", v)}
                error={formErrors.state}
                placeholder="Maharashtra"
              />
              <InputField
                label="Pincode"
                value={address.pincode}
                onChange={(v) => updateAddress("pincode", v)}
                error={formErrors.pincode}
                placeholder="400001"
              />
            </div>
          </section>

          {/* Payment Method */}
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">💳 Payment Method</h2>
            <div className="space-y-2">
              {PAYMENT_METHODS.map((method) => (
                <label
                  key={method.value}
                  className={cn(
                    "flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors",
                    paymentMethod === method.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-slate-200 hover:bg-slate-50"
                  )}
                >
                  <input
                    type="radio"
                    name="payment"
                    value={method.value}
                    checked={paymentMethod === method.value}
                    onChange={() => {
                      setPaymentMethod(method.value);
                      setUpiConfirmed(false);
                    }}
                    className="h-4 w-4 text-blue-600"
                  />
                  <span className="text-lg">{method.icon}</span>
                  <span className="text-sm font-medium text-slate-700">{method.label}</span>
                </label>
              ))}
            </div>

            {/* UPI QR Section */}
            {paymentMethod === "upi" && (
              <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <div className="mx-auto mb-3 h-40 w-40 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                  <div className="grid grid-cols-5 grid-rows-5 gap-0.5 h-32 w-32">
                    {Array.from({ length: 25 }).map((_, i) => (
                      <div
                        key={i}
                        className={cn(
                          "rounded-sm",
                          Math.random() > 0.4 ? "bg-slate-900" : "bg-white"
                        )}
                      />
                    ))}
                  </div>
                </div>
                <p className="text-sm text-slate-600 mb-3">Scan QR code to pay {formatPrice(totalPayable)}</p>
                {upiConfirmed ? (
                  <div className="inline-flex items-center gap-2 rounded-full bg-green-100 px-4 py-2 text-sm font-medium text-green-700">
                    ✓ Payment Confirmed
                  </div>
                ) : (
                  <button
                    onClick={() => setUpiConfirmed(true)}
                    className="rounded-lg bg-green-600 px-6 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
                  >
                    Payment Done (Demo)
                  </button>
                )}
              </div>
            )}
          </section>
        </div>

        {/* Order Summary Sidebar */}
        <div className="lg:col-span-1">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sticky top-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Order Summary</h2>

            <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm">
                  <span className="text-slate-600 truncate pr-2">
                    {item.product_name} × {item.quantity}
                  </span>
                  <span className="text-slate-900 font-medium whitespace-nowrap">
                    {formatPrice(item.line_total)}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-200 pt-3 space-y-2 text-sm">
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
                  <span>Total</span>
                  <span>{formatPrice(totalPayable)}</span>
                </div>
              </div>
            </div>

            <button
              onClick={handlePlaceOrder}
              disabled={loading}
              className={cn(
                "mt-6 w-full rounded-lg py-3 text-sm font-semibold text-white transition-colors",
                "bg-green-600 hover:bg-green-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
              )}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Placing Order...
                </span>
              ) : (
                "Place Order"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Input Field Component
// ---------------------------------------------------------------------------

function InputField({
  label,
  value,
  onChange,
  error,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          "w-full rounded-lg border px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500",
          error ? "border-red-300 bg-red-50" : "border-slate-300"
        )}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
