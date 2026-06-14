"use client";

import { useCallback } from "react";
import * as memoryService from "@/services/memory.service";
import { useMemoryStore } from "@/stores/memory.store";
import { useUserStore } from "@/stores/user.store";
import type { UserMemory, BudgetLevel } from "@/types/memory";

/**
 * Memory hook — manages user preferences with API sync.
 */
export function useMemory() {
  const userId = useUserStore((s) => s.userId);
  const {
    memory,
    isLoaded,
    lastUpdated,
    setMemory,
    updatePreferences,
    addDietaryPreference: addDietLocal,
    removeDietaryPreference: removeDietLocal,
    addPreferredBrand: addBrandLocal,
    removePreferredBrand: removeBrandLocal,
    setBudgetLevel: setBudgetLocal,
    setFamilySize: setFamilySizeLocal,
    resetMemory,
    markLoaded,
  } = useMemoryStore();

  // ── Fetch from backend ─────────────────────────────────────

  const fetchMemory = useCallback(async (): Promise<UserMemory | null> => {
    try {
      const data = await memoryService.getMemory(userId);
      setMemory(data.memory);
      return data.memory;
    } catch {
      markLoaded(); // Mark loaded even on error (empty memory)
      return null;
    }
  }, [userId, setMemory, markLoaded]);

  // ── Save to backend ────────────────────────────────────────

  const saveMemory = useCallback(
    async (updates: Partial<UserMemory>): Promise<boolean> => {
      try {
        const data = await memoryService.storeMemory(userId, updates);
        setMemory(data.memory);
        return true;
      } catch {
        return false;
      }
    },
    [userId, setMemory]
  );

  // ── Granular updates (local + remote sync) ─────────────────

  const addDietaryPreference = useCallback(
    async (pref: string) => {
      addDietLocal(pref);
      await memoryService.addDietaryPreference(userId, pref).catch(() => {});
    },
    [userId, addDietLocal]
  );

  const removeDietaryPreference = useCallback(
    async (pref: string) => {
      removeDietLocal(pref);
      const updated = memory.dietary_preferences.filter((p) => p !== pref);
      await memoryService.storeMemory(userId, { dietary_preferences: updated }).catch(() => {});
    },
    [userId, memory.dietary_preferences, removeDietLocal]
  );

  const addPreferredBrand = useCallback(
    async (brand: string) => {
      addBrandLocal(brand);
      await memoryService.addPreferredBrand(userId, brand).catch(() => {});
    },
    [userId, addBrandLocal]
  );

  const removePreferredBrand = useCallback(
    async (brand: string) => {
      removeBrandLocal(brand);
      const updated = memory.preferred_brands.filter((b) => b !== brand);
      await memoryService.storeMemory(userId, { preferred_brands: updated }).catch(() => {});
    },
    [userId, memory.preferred_brands, removeBrandLocal]
  );

  const setBudgetLevel = useCallback(
    async (level: BudgetLevel | null) => {
      setBudgetLocal(level);
      if (level) await memoryService.setBudgetLevel(userId, level).catch(() => {});
    },
    [userId, setBudgetLocal]
  );

  const setFamilySize = useCallback(
    async (size: number | null) => {
      setFamilySizeLocal(size);
      await memoryService.storeMemory(userId, { family_size: size }).catch(() => {});
    },
    [userId, setFamilySizeLocal]
  );

  const clearMemory = useCallback(async () => {
    try {
      await memoryService.clearMemory(userId);
      resetMemory();
      return true;
    } catch {
      return false;
    }
  }, [userId, resetMemory]);

  return {
    // State
    memory,
    isLoaded,
    lastUpdated,
    // Actions
    fetchMemory,
    saveMemory,
    addDietaryPreference,
    removeDietaryPreference,
    addPreferredBrand,
    removePreferredBrand,
    setBudgetLevel,
    setFamilySize,
    clearMemory,
  };
}
