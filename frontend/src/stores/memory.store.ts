/**
 * Memory Store — manages user preferences and memory state.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserMemory, BudgetLevel } from "@/types/memory";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MemoryState {
  // State
  memory: UserMemory;
  lastUpdated: string | null;
  isLoaded: boolean;

  // Actions
  setMemory: (memory: UserMemory) => void;
  updatePreferences: (updates: Partial<UserMemory>) => void;
  addDietaryPreference: (pref: string) => void;
  removeDietaryPreference: (pref: string) => void;
  addPreferredBrand: (brand: string) => void;
  removePreferredBrand: (brand: string) => void;
  setBudgetLevel: (level: BudgetLevel | null) => void;
  setFamilySize: (size: number | null) => void;
  setSustainabilityScore: (score: number) => void;
  resetMemory: () => void;
  markLoaded: () => void;
}

// ---------------------------------------------------------------------------
// Default
// ---------------------------------------------------------------------------

const DEFAULT_MEMORY: UserMemory = {
  dietary_preferences: [],
  preferred_brands: [],
  budget_level: null,
  family_size: null,
  purchase_patterns: [],
  sustainability_score: 0,
};

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useMemoryStore = create<MemoryState>()(
  persist(
    (set) => ({
      // Initial state
      memory: { ...DEFAULT_MEMORY },
      lastUpdated: null,
      isLoaded: false,

      // Actions
      setMemory: (memory) =>
        set({ memory, lastUpdated: new Date().toISOString(), isLoaded: true }),

      updatePreferences: (updates) =>
        set((state) => ({
          memory: { ...state.memory, ...updates },
          lastUpdated: new Date().toISOString(),
        })),

      addDietaryPreference: (pref) =>
        set((state) => ({
          memory: {
            ...state.memory,
            dietary_preferences: [...new Set([...state.memory.dietary_preferences, pref])],
          },
          lastUpdated: new Date().toISOString(),
        })),

      removeDietaryPreference: (pref) =>
        set((state) => ({
          memory: {
            ...state.memory,
            dietary_preferences: state.memory.dietary_preferences.filter((p) => p !== pref),
          },
          lastUpdated: new Date().toISOString(),
        })),

      addPreferredBrand: (brand) =>
        set((state) => ({
          memory: {
            ...state.memory,
            preferred_brands: [...new Set([...state.memory.preferred_brands, brand])],
          },
          lastUpdated: new Date().toISOString(),
        })),

      removePreferredBrand: (brand) =>
        set((state) => ({
          memory: {
            ...state.memory,
            preferred_brands: state.memory.preferred_brands.filter((b) => b !== brand),
          },
          lastUpdated: new Date().toISOString(),
        })),

      setBudgetLevel: (level) =>
        set((state) => ({
          memory: { ...state.memory, budget_level: level },
          lastUpdated: new Date().toISOString(),
        })),

      setFamilySize: (size) =>
        set((state) => ({
          memory: { ...state.memory, family_size: size },
          lastUpdated: new Date().toISOString(),
        })),

      setSustainabilityScore: (score) =>
        set((state) => ({
          memory: { ...state.memory, sustainability_score: score },
          lastUpdated: new Date().toISOString(),
        })),

      resetMemory: () =>
        set({ memory: { ...DEFAULT_MEMORY }, lastUpdated: null, isLoaded: false }),

      markLoaded: () => set({ isLoaded: true }),
    }),
    {
      name: "neednow-memory",
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

export const selectMemory = (state: MemoryState) => state.memory;
export const selectIsMemoryLoaded = (state: MemoryState) => state.isLoaded;
export const selectDietaryPreferences = (state: MemoryState) => state.memory.dietary_preferences;
export const selectPreferredBrands = (state: MemoryState) => state.memory.preferred_brands;
export const selectBudgetLevel = (state: MemoryState) => state.memory.budget_level;
export const selectFamilySize = (state: MemoryState) => state.memory.family_size;
export const selectSustainabilityScore = (state: MemoryState) => state.memory.sustainability_score;
export const selectLastUpdated = (state: MemoryState) => state.lastUpdated;
