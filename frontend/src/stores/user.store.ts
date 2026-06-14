/**
 * User Store — manages authentication and user profile state.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface UserProfile {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  city: string | null;
}

interface UserState {
  // State
  userId: string;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  token: string | null;

  // Actions
  setUser: (profile: UserProfile, token?: string) => void;
  setToken: (token: string) => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
  logout: () => void;
}

// ---------------------------------------------------------------------------
// Default (demo user for hackathon)
// ---------------------------------------------------------------------------

const DEFAULT_USER_ID = "550e8400-e29b-41d4-a716-446655440000";

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      // Initial state
      userId: DEFAULT_USER_ID,
      profile: null,
      isAuthenticated: false,
      token: null,

      // Actions
      setUser: (profile, token) =>
        set({
          userId: profile.id,
          profile,
          isAuthenticated: true,
          token: token ?? null,
        }),

      setToken: (token) => set({ token, isAuthenticated: true }),

      updateProfile: (updates) =>
        set((state) => ({
          profile: state.profile ? { ...state.profile, ...updates } : null,
        })),

      logout: () =>
        set({
          userId: DEFAULT_USER_ID,
          profile: null,
          isAuthenticated: false,
          token: null,
        }),
    }),
    {
      name: "neednow-user",
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

export const selectUserId = (state: UserState) => state.userId;
export const selectProfile = (state: UserState) => state.profile;
export const selectIsAuthenticated = (state: UserState) => state.isAuthenticated;
export const selectUserName = (state: UserState) => state.profile?.name ?? "Guest";
export const selectToken = (state: UserState) => state.token;
