import { create } from "zustand";

interface UserState {
  userId: string;
  name: string | null;
  setUser: (userId: string, name?: string) => void;
  clearUser: () => void;
}

const DEFAULT_USER_ID = "550e8400-e29b-41d4-a716-446655440000";

export const useUserStore = create<UserState>((set) => ({
  userId: DEFAULT_USER_ID,
  name: null,
  setUser: (userId, name) => set({ userId, name: name ?? null }),
  clearUser: () => set({ userId: DEFAULT_USER_ID, name: null }),
}));
