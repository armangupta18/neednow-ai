/**
 * Memory Service — connects to memory store/retrieve/clear APIs.
 */

import { apiPost, apiGet, apiDelete } from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";
import type {
  UserMemory,
  MemoryResponse,
  StoreMemoryRequest,
  ClearMemoryResponse,
} from "@/types/memory";

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

/** Get a user's stored memory/preferences */
export async function getMemory(userId: string): Promise<MemoryResponse> {
  return apiGet<MemoryResponse>(API_ROUTES.MEMORY.GET(userId));
}

/** Store or update user memory/preferences */
export async function storeMemory(
  userId: string,
  memory: Partial<UserMemory>
): Promise<MemoryResponse> {
  const request: StoreMemoryRequest = {
    user_id: userId,
    memory,
  };
  return apiPost<MemoryResponse>(API_ROUTES.MEMORY.STORE, request);
}

/** Clear all memory for a user (reset to defaults) */
export async function clearMemory(userId: string): Promise<ClearMemoryResponse> {
  return apiDelete<ClearMemoryResponse>(API_ROUTES.MEMORY.CLEAR(userId));
}

// ---------------------------------------------------------------------------
// Convenience Functions
// ---------------------------------------------------------------------------

/** Update a single preference field */
export async function updatePreference<K extends keyof UserMemory>(
  userId: string,
  key: K,
  value: UserMemory[K]
): Promise<MemoryResponse> {
  return storeMemory(userId, { [key]: value });
}

/** Add a dietary preference */
export async function addDietaryPreference(
  userId: string,
  preference: string
): Promise<MemoryResponse> {
  const current = await getMemory(userId);
  const updated = [...new Set([...current.memory.dietary_preferences, preference])];
  return storeMemory(userId, { dietary_preferences: updated });
}

/** Add a preferred brand */
export async function addPreferredBrand(
  userId: string,
  brand: string
): Promise<MemoryResponse> {
  const current = await getMemory(userId);
  const updated = [...new Set([...current.memory.preferred_brands, brand])];
  return storeMemory(userId, { preferred_brands: updated });
}

/** Set budget level */
export async function setBudgetLevel(
  userId: string,
  level: "low" | "medium" | "high" | "premium"
): Promise<MemoryResponse> {
  return storeMemory(userId, { budget_level: level });
}
