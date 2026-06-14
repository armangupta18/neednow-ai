import api from "./api";
import { ENDPOINTS } from "@/constants/api";
import type { MemoryResponse, StoreMemoryRequest } from "@/types/memory";

export async function storeMemory(request: StoreMemoryRequest) {
  const response = await api.post<MemoryResponse>(ENDPOINTS.MEMORY.STORE, request);
  return response.data;
}

export async function getMemory(userId: string) {
  const response = await api.get<MemoryResponse>(ENDPOINTS.MEMORY.GET(userId));
  return response.data;
}

export async function clearMemory(userId: string) {
  const response = await api.delete(ENDPOINTS.MEMORY.CLEAR(userId));
  return response.data;
}
