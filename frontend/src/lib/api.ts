/**
 * Centralized API client for NeedNow AI.
 *
 * Features:
 * - Axios instance with configurable baseURL and timeout
 * - Request interceptor: injects auth token
 * - Response interceptor: normalizes errors
 * - Typed error extraction
 * - Request cancellation helpers
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import { getToken } from "./auth";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const API_TIMEOUT = 30_000;

// Log the API base URL in development
if (typeof window !== "undefined") {
  console.log("[NeedNow API] Base URL:", API_BASE_URL);
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
// Axios Instance
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
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response Interceptor
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    const status = error.response?.status ?? 500;
    const data: ApiErrorResponse = error.response?.data ?? {
      detail: error.message || "Network error",
    };

    // Handle 401 — clear token and redirect
    if (status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        // Optionally redirect to login
      }
    }

    return Promise.reject(new ApiError(status, data));
  }
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create an AbortController for request cancellation */
export function createAbortController(): AbortController {
  return new AbortController();
}

/** Typed GET helper */
export async function apiGet<T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.get<T>(url, config);
  return response.data;
}

/** Typed POST helper */
export async function apiPost<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.post<T>(url, data, config);
  return response.data;
}

/** Typed DELETE helper */
export async function apiDelete<T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await api.delete<T>(url, config);
  return response.data;
}

export default api;
