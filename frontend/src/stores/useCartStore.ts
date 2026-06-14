import { create } from "zustand";
import type { CartItem } from "@/services/cartApi";

interface CartState {
  cartId: string | null;
  items: CartItem[];
  totalAmount: number;
  setCart: (cartId: string, items: CartItem[], total: number) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartState>((set) => ({
  cartId: null,
  items: [],
  totalAmount: 0,
  setCart: (cartId, items, total) => set({ cartId, items, totalAmount: total }),
  clearCart: () => set({ cartId: null, items: [], totalAmount: 0 }),
}));
