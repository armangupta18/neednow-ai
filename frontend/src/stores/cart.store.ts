/**
 * Cart Store — manages shopping cart state with persistence.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { CartItem } from "@/types/cart";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CartState {
  // State
  cartId: string | null;
  userId: string | null;
  items: CartItem[];
  totalAmount: number;

  // Actions
  setCart: (cartId: string, userId: string, items: CartItem[], total: number) => void;
  addItem: (item: CartItem) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      // Initial state
      cartId: null,
      userId: null,
      items: [],
      totalAmount: 0,

      // Actions
      setCart: (cartId, userId, items, total) =>
        set({ cartId, userId, items, totalAmount: total }),

      addItem: (item) =>
        set((state) => {
          const existing = state.items.find((i) => i.product_id === item.product_id);
          if (existing) {
            const updated = state.items.map((i) =>
              i.product_id === item.product_id
                ? { ...i, quantity: i.quantity + item.quantity, line_total: (i.quantity + item.quantity) * i.unit_price }
                : i
            );
            return { items: updated, totalAmount: updated.reduce((s, i) => s + i.line_total, 0) };
          }
          const items = [...state.items, item];
          return { items, totalAmount: items.reduce((s, i) => s + i.line_total, 0) };
        }),

      removeItem: (productId) =>
        set((state) => {
          const items = state.items.filter((i) => i.product_id !== productId);
          return { items, totalAmount: items.reduce((s, i) => s + i.line_total, 0) };
        }),

      updateQuantity: (productId, quantity) =>
        set((state) => {
          const items = state.items.map((i) =>
            i.product_id === productId
              ? { ...i, quantity, line_total: quantity * i.unit_price }
              : i
          );
          return { items, totalAmount: items.reduce((s, i) => s + i.line_total, 0) };
        }),

      clearCart: () => set({ cartId: null, items: [], totalAmount: 0 }),
    }),
    {
      name: "neednow-cart",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      ),
    }
  )
);

// ---------------------------------------------------------------------------
// Selectors
// ---------------------------------------------------------------------------

export const selectCartItems = (state: CartState) => state.items;
export const selectCartTotal = (state: CartState) => state.totalAmount;
export const selectCartItemCount = (state: CartState) =>
  state.items.reduce((sum, i) => sum + i.quantity, 0);
export const selectIsInCart = (productId: string) => (state: CartState) =>
  state.items.some((i) => i.product_id === productId);
export const selectCartItem = (productId: string) => (state: CartState) =>
  state.items.find((i) => i.product_id === productId);
