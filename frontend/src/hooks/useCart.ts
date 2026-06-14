"use client";

import { useState, useCallback } from "react";
import * as cartService from "@/services/cart.service";
import { useCartStore } from "@/stores/cart.store";
import { useUserStore } from "@/stores/user.store";

/**
 * Cart hook — manages cart state with API sync.
 */
export function useCart() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const userId = useUserStore((s) => s.userId);
  const { items, totalAmount, cartId, setCart, removeItem, clearCart } = useCartStore();

  const fetchCart = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await cartService.getCart(userId);
      setCart(data.cart_id, userId, data.items, data.total_amount);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load cart");
    } finally {
      setLoading(false);
    }
  }, [userId, setCart]);

  const addItem = useCallback(
    async (productId: string, quantity = 1) => {
      try {
        setLoading(true);
        setError(null);
        const data = await cartService.addToCart(userId, productId, quantity);
        setCart(data.cart.cart_id, userId, data.cart.items, data.cart.total_amount);
        return true;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to add item");
        return false;
      } finally {
        setLoading(false);
      }
    },
    [userId, setCart]
  );

  const removeCartItem = useCallback(
    async (productId: string) => {
      try {
        setLoading(true);
        setError(null);
        const data = await cartService.removeFromCart(userId, productId);
        setCart(data.cart.cart_id, userId, data.cart.items, data.cart.total_amount);
        return true;
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to remove item");
        return false;
      } finally {
        setLoading(false);
      }
    },
    [userId, setCart]
  );

  const emptyCart = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await cartService.clearCart(userId);
      clearCart();
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to clear cart");
      return false;
    } finally {
      setLoading(false);
    }
  }, [userId, clearCart]);

  const itemCount = items.reduce((sum, i) => sum + i.quantity, 0);

  return {
    // State
    items,
    totalAmount,
    cartId,
    itemCount,
    loading,
    error,
    // Actions
    fetchCart,
    addItem,
    removeItem: removeCartItem,
    emptyCart,
  };
}
