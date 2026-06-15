/**
 * Centralized API client for NeedNow AI.
 *
 * Single Axios instance — the ONLY place axios.create() is called.
 * baseURL = NEXT_PUBLIC_API_URL (bare domain, no /api/v1).
 * All endpoint paths in src/constants/api.ts include the /api/v1 prefix.
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import { getToken } from "./auth";
import { API_BASE_URL, API_TIMEOUT } from "@/constants/api";

// Debug log so the base URL is visible in browser console during deployment
if (typeof window !== "undefined") {
  console.log("[API BASE URL]", API_BASE_URL);
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
  field_errors?: Array<{ field: string; message: string }>;
}

export class ApiError extends Error {
  status: number;
  data: ApiErrorResponse;

  constructor(status: number, data: ApiErrorResponse) {
    super(data.detail || data.message || data.error || "Request failed");
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

// ---------------------------------------------------------------------------
// Axios Instance — only one in the entire app
// ---------------------------------------------------------------------------

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ---------------------------------------------------------------------------
// Request Interceptor
// ---------------------------------------------------------------------------

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Debug logs (visible in browser DevTools → Console)
    if (typeof window !== "undefined") {
      console.log("[REQUEST METHOD]", config.method?.toUpperCase());
      console.log("[REQUEST URL]", (config.baseURL ?? "") + (config.url ?? ""));
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response Interceptor
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response) => {
    if (typeof window !== "undefined") {
      console.log(`[API] ✓ ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    }
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    const status = error.response?.status ?? 500;
    const data: ApiErrorResponse = error.response?.data ?? {
      detail: error.message || "Network error",
    };

    if (typeof window !== "undefined") {
      console.error(`[API] ✗ ${status} ${error.config?.method?.toUpperCase()} ${error.config?.url}`);
    }

    // Handle 401 — clear token
    if (status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
    }

    return Promise.reject(new ApiError(status, data));
  }
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function createAbortController(): AbortController {
  return new AbortController();
}

export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.get<T>(url, config);
  return response.data;
}

export async function apiPost<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.post<T>(url, data, config);
  return response.data;
}

export async function apiDelete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await api.delete<T>(url, config);
  return response.data;
}

export default api;
